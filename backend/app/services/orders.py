"""Order lifecycle: cart, checkout, payment confirmation, artwork review, production and refunds.

Order status flow:
  cart -> pending_payment -> paid -> in_review <-> awaiting_customer -> approved -> in_production -> shipped -> completed
  Any paid order can be refunded by an admin; unpaid orders are cancelled.

Item artwork flow:
  awaiting_artwork -> submitted -> (approved | rejected | proof_sent)
  rejected -> submitted (customer re-uploads)
  proof_sent -> approved (customer approves) | changes_requested -> proof_sent (admin sends new proof)
"""

from datetime import datetime, timezone

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    Artwork,
    ArtworkKind,
    ArtworkStatus,
    DesignService,
    Order,
    OrderEvent,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentStatus,
    Product,
    User,
)
from app.services import artwork as artwork_service
from app.services import notifications
from app.services.payments import get_payment_provider
from app.services.pricing import quote_item
from app.services.storage import get_storage


class OrderError(ValueError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


ORDER_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.cart: {OrderStatus.pending_payment, OrderStatus.cancelled},
    OrderStatus.pending_payment: {OrderStatus.paid, OrderStatus.cart, OrderStatus.cancelled},
    OrderStatus.paid: {OrderStatus.in_review, OrderStatus.refunded},
    OrderStatus.in_review: {OrderStatus.awaiting_customer, OrderStatus.approved, OrderStatus.refunded},
    OrderStatus.awaiting_customer: {OrderStatus.in_review, OrderStatus.approved, OrderStatus.refunded},
    OrderStatus.approved: {OrderStatus.in_production, OrderStatus.in_review, OrderStatus.refunded},
    OrderStatus.in_production: {OrderStatus.shipped, OrderStatus.refunded},
    OrderStatus.shipped: {OrderStatus.completed},
    OrderStatus.completed: set(),
    OrderStatus.cancelled: set(),
    OrderStatus.refunded: set(),
}

EDITABLE_CART_STATUSES = {OrderStatus.cart, OrderStatus.pending_payment}
REVIEW_STATUSES = {OrderStatus.in_review, OrderStatus.awaiting_customer, OrderStatus.approved}
PAID_STATUSES = {
    OrderStatus.paid,
    OrderStatus.in_review,
    OrderStatus.awaiting_customer,
    OrderStatus.approved,
    OrderStatus.in_production,
}


def record_event(db: Session, order: Order, event_type: str, actor: User | None = None, item: OrderItem | None = None,
                 from_status: str | None = None, to_status: str | None = None, note: str | None = None) -> OrderEvent:
    ev = OrderEvent(
        order_id=order.id,
        item_id=item.id if item else None,
        actor_id=actor.id if actor else None,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        note=note,
    )
    db.add(ev)
    return ev


def transition(db: Session, order: Order, to: OrderStatus, actor: User | None = None, note: str | None = None,
               event_type: str = "status_changed") -> None:
    if to not in ORDER_TRANSITIONS.get(order.status, set()):
        raise OrderError(f"Cannot move order from '{order.status.value}' to '{to.value}'", 409)
    record_event(db, order, event_type, actor=actor, from_status=order.status.value, to_status=to.value, note=note)
    order.status = to


# ---------- cart ----------

def get_or_create_cart(db: Session, user: User) -> Order:
    # a checkout that is still awaiting payment keeps the cart locked until it is paid or reopened
    cart = (
        db.query(Order)
        .filter(Order.user_id == user.id, Order.status.in_([OrderStatus.cart, OrderStatus.pending_payment]))
        .order_by(Order.created_at.desc())
        .first()
    )
    if cart is None:
        cart = Order(user_id=user.id, currency=get_settings().currency)
        db.add(cart)
        db.flush()
    return cart


def _price_item(item: OrderItem, product: Product, quantity: int, width_in, height_in, size_preset, options) -> None:
    q = quote_item(product, quantity, width_in, height_in, size_preset, options)
    item.quantity = q.quantity
    item.width_in = q.width_in
    item.height_in = q.height_in
    item.size_preset = q.size_preset
    item.selected_options = q.resolved_options
    item.unit_price_cents = q.unit_price_cents
    item.line_total_cents = q.line_total_cents
    item.price_breakdown = q.breakdown


def recompute_totals(order: Order) -> None:
    s = get_settings()
    order.subtotal_cents = sum(i.line_total_cents for i in order.items)
    rates = {"standard": s.shipping_standard_cents, "express": s.shipping_express_cents}
    order.shipping_cents = rates.get(order.shipping_method or "", 0)
    order.total_cents = order.subtotal_cents + order.shipping_cents


def add_item(db: Session, cart: Order, product: Product, quantity: int, width_in, height_in, size_preset, options,
             design_service: DesignService, instructions: str | None) -> OrderItem:
    if cart.status != OrderStatus.cart:
        raise OrderError("Cart is locked while payment is pending; reopen the order to edit it", 409)
    item = OrderItem(order_id=cart.id, product_id=product.id, design_service=design_service, customer_instructions=instructions)
    _price_item(item, product, quantity, width_in, height_in, size_preset, options)
    db.add(item)
    cart.items.append(item)
    recompute_totals(cart)
    return item


def update_item(db: Session, cart: Order, item: OrderItem, quantity, width_in, height_in, size_preset, options,
                design_service, instructions) -> OrderItem:
    if cart.status != OrderStatus.cart:
        raise OrderError("Cart is locked while payment is pending; reopen the order to edit it", 409)
    _price_item(
        item,
        item.product,
        quantity if quantity is not None else item.quantity,
        width_in if width_in is not None else item.width_in,
        height_in if height_in is not None else item.height_in,
        size_preset if size_preset is not None else item.size_preset,
        options if options is not None else item.selected_options,
    )
    if design_service is not None:
        item.design_service = design_service
    if instructions is not None:
        item.customer_instructions = instructions
    # size changes invalidate the preflight of existing artwork, so re-run it
    for art in item.artworks:
        if art.kind == ArtworkKind.customer_upload:
            art.warnings = artwork_service.preflight_warnings(
                dict(art.file_metadata), item.width_in, item.height_in, item.product.pricing_config.get("min_dpi")
            )
    recompute_totals(cart)
    return item


def remove_item(db: Session, cart: Order, item: OrderItem) -> None:
    if cart.status != OrderStatus.cart:
        raise OrderError("Cart is locked while payment is pending; reopen the order to edit it", 409)
    cart.items.remove(item)
    db.delete(item)
    recompute_totals(cart)


# ---------- artwork ----------

def customer_can_upload(order: Order, item: OrderItem) -> bool:
    if order.status == OrderStatus.cart:
        return True
    if order.status in {OrderStatus.paid, OrderStatus.in_review, OrderStatus.awaiting_customer}:
        return item.artwork_status in {ArtworkStatus.awaiting_artwork, ArtworkStatus.rejected, ArtworkStatus.submitted}
    return False


def attach_artwork(db: Session, order: Order, item: OrderItem, data: bytes, filename: str, uploader: User,
                   kind: ArtworkKind = ArtworkKind.customer_upload, note: str | None = None) -> Artwork:
    s = get_settings()
    product = item.product
    allowed = product.pricing_config.get("allowed_file_types") or artwork_service.DEFAULT_ALLOWED
    info = artwork_service.inspect(data, filename, allowed=allowed, max_bytes=s.max_upload_bytes)
    warnings = []
    if kind == ArtworkKind.customer_upload:
        warnings = artwork_service.preflight_warnings(info.metadata, item.width_in, item.height_in, product.pricing_config.get("min_dpi"))

    version = 1 + max((a.version for a in item.artworks if a.kind == kind), default=0)
    storage = get_storage()
    base = f"orders/{order.id}/items/{item.id}/{kind.value}/v{version}"
    key = storage.save(f"{base}/{artwork_service.safe_filename(filename)}", data, info.content_type)
    preview_key = storage.save(f"{base}/preview.jpg", info.preview, "image/jpeg") if info.preview else None

    art = Artwork(
        item_id=item.id,
        kind=kind,
        version=version,
        storage_key=key,
        preview_key=preview_key,
        original_filename=filename,
        content_type=info.content_type,
        size_bytes=len(data),
        file_metadata=info.metadata,
        warnings=warnings,
        note=note,
        uploaded_by_id=uploader.id,
    )
    db.add(art)
    item.artworks.append(art)
    return art


def customer_upload(db: Session, order: Order, item: OrderItem, data: bytes, filename: str, user: User) -> Artwork:
    if not customer_can_upload(order, item):
        raise OrderError("Artwork cannot be changed for this item at this stage", 409)
    art = attach_artwork(db, order, item, data, filename, user)
    prev = item.artwork_status
    item.artwork_status = ArtworkStatus.submitted
    item.review_note = None
    if item.design_service != DesignService.upload:
        item.design_service = DesignService.upload
    record_event(db, order, "artwork_uploaded", actor=user, item=item, from_status=prev.value,
                 to_status=item.artwork_status.value, note=f"v{art.version} {filename}")
    if order.status in REVIEW_STATUSES:
        sync_review_status(db, order, actor=user)
    return art


# ---------- checkout and payment ----------

def checkout(db: Session, order: Order, user: User, shipping_method: str, shipping_address: dict, note: str | None) -> Payment:
    if order.status not in EDITABLE_CART_STATUSES:
        raise OrderError("Order is not a cart", 409)
    if not order.items:
        raise OrderError("Cart is empty")
    for item in order.items:
        if item.design_service == DesignService.upload and item.artwork_status == ArtworkStatus.awaiting_artwork:
            raise OrderError(f"Item '{item.product.name}' needs artwork, or choose to design later")
    if shipping_method not in {"standard", "express"}:
        raise OrderError("shipping_method must be 'standard' or 'express'")
    # re-price against the current catalog so a stale cart cannot carry an old price
    for item in order.items:
        _price_item(item, item.product, item.quantity, item.width_in, item.height_in, item.size_preset, item.selected_options)
    order.shipping_method = shipping_method
    order.shipping_address = shipping_address
    order.customer_note = note
    recompute_totals(order)
    if order.total_cents <= 0:
        raise OrderError("Order total must be positive")

    provider = get_payment_provider()
    s = get_settings()
    front = s.frontend_url.rstrip("/")
    result = provider.create_checkout(
        order,
        order.total_cents,
        order.currency,
        success_url=f"{front}/orders/{order.id}?paid=1",
        cancel_url=f"{front}/cart?cancelled=1",
        customer_email=user.email,
    )
    payment = Payment(
        order_id=order.id,
        provider=provider.name,
        checkout_session_id=result.session_id,
        payment_intent_id=result.payment_intent_id,
        checkout_url=result.url,
        amount_cents=order.total_cents,
        currency=order.currency,
    )
    db.add(payment)
    order.payments.append(payment)
    if order.status == OrderStatus.cart:
        transition(db, order, OrderStatus.pending_payment, actor=user, event_type="checkout_started")
    else:
        record_event(db, order, "checkout_restarted", actor=user)
    return payment


def reopen_cart(db: Session, order: Order, user: User) -> None:
    if order.status != OrderStatus.pending_payment:
        raise OrderError("Only an order awaiting payment can be reopened", 409)
    transition(db, order, OrderStatus.cart, actor=user, event_type="checkout_abandoned")


def confirm_payment(db: Session, payment: Payment, payment_intent_id: str | None, background: BackgroundTasks | None = None) -> Order:
    """Idempotent: a second webhook for the same session is a no-op."""
    order = payment.order
    if payment.status == PaymentStatus.paid:
        return order
    payment.status = PaymentStatus.paid
    if payment_intent_id:
        payment.payment_intent_id = payment_intent_id
    if order.status == OrderStatus.pending_payment:
        order.placed_at = datetime.now(timezone.utc)
        transition(db, order, OrderStatus.paid, event_type="payment_confirmed", note=payment.checkout_session_id)
        transition(db, order, OrderStatus.in_review, event_type="review_started")
        if background is not None:
            background.add_task(notifications.notify_order_paid, order.user.email, order.id, order.total_cents, order.currency)
    return order


def paid_payment(order: Order) -> Payment | None:
    return next((p for p in order.payments if p.status == PaymentStatus.paid), None)


def cancel_or_refund(db: Session, order: Order, admin: User, reason: str | None, background: BackgroundTasks | None = None) -> Order:
    payment = paid_payment(order)
    if payment is None:
        if order.status not in EDITABLE_CART_STATUSES:
            raise OrderError("Order has no paid payment to refund", 409)
        transition(db, order, OrderStatus.cancelled, actor=admin, note=reason, event_type="cancelled")
        return order
    if order.status not in PAID_STATUSES:
        raise OrderError(f"Order in '{order.status.value}' cannot be refunded", 409)
    provider = get_payment_provider()
    refund_id = provider.refund(payment, payment.amount_cents)
    payment.refund_id = refund_id
    payment.refunded_cents = payment.amount_cents
    payment.status = PaymentStatus.refunded
    transition(db, order, OrderStatus.refunded, actor=admin, note=reason, event_type="refunded")
    if background is not None:
        background.add_task(notifications.notify_order_refunded, order.user.email, order.id, payment.amount_cents, payment.currency, reason)
    return order


# ---------- review ----------

def sync_review_status(db: Session, order: Order, actor: User | None = None, background: BackgroundTasks | None = None) -> None:
    """Derive the order status from its items after any review action."""
    if order.status not in REVIEW_STATUSES:
        return
    statuses = {i.artwork_status for i in order.items}
    if statuses <= {ArtworkStatus.approved}:
        target = OrderStatus.approved
    elif statuses & {ArtworkStatus.rejected, ArtworkStatus.proof_sent}:
        target = OrderStatus.awaiting_customer
    else:
        target = OrderStatus.in_review
    if target != order.status:
        transition(db, order, target, actor=actor, event_type="review_status_synced")
        if target == OrderStatus.approved and background is not None:
            background.add_task(notifications.notify_order_approved, order.user.email, order.id)


def _require_reviewable(order: Order) -> None:
    if order.status not in REVIEW_STATUSES:
        raise OrderError(f"Order in '{order.status.value}' is not under review", 409)


def approve_artwork(db: Session, order: Order, item: OrderItem, admin: User, note: str | None, background: BackgroundTasks) -> None:
    _require_reviewable(order)
    if item.artwork_status not in {ArtworkStatus.submitted, ArtworkStatus.proof_sent, ArtworkStatus.changes_requested}:
        raise OrderError(f"Item artwork is '{item.artwork_status.value}', nothing to approve", 409)
    prev = item.artwork_status
    item.artwork_status = ArtworkStatus.approved
    item.review_note = note
    record_event(db, order, "artwork_approved", actor=admin, item=item, from_status=prev.value, to_status="approved", note=note)
    sync_review_status(db, order, actor=admin, background=background)


def reject_artwork(db: Session, order: Order, item: OrderItem, admin: User, reason: str, background: BackgroundTasks) -> None:
    _require_reviewable(order)
    if item.artwork_status not in {ArtworkStatus.submitted, ArtworkStatus.changes_requested, ArtworkStatus.proof_sent}:
        raise OrderError(f"Item artwork is '{item.artwork_status.value}', cannot reject", 409)
    prev = item.artwork_status
    item.artwork_status = ArtworkStatus.rejected
    item.review_note = reason
    record_event(db, order, "artwork_rejected", actor=admin, item=item, from_status=prev.value, to_status="rejected", note=reason)
    sync_review_status(db, order, actor=admin, background=background)
    background.add_task(notifications.notify_artwork_rejected, order.user.email, order.id, item.product.name, reason)


def send_proof(db: Session, order: Order, item: OrderItem, admin: User, data: bytes, filename: str, note: str | None,
               background: BackgroundTasks) -> Artwork:
    _require_reviewable(order)
    if item.artwork_status in {ArtworkStatus.approved}:
        raise OrderError("Item is already approved", 409)
    proof = attach_artwork(db, order, item, data, filename, admin, kind=ArtworkKind.proof, note=note)
    prev = item.artwork_status
    item.artwork_status = ArtworkStatus.proof_sent
    item.review_note = note
    record_event(db, order, "proof_sent", actor=admin, item=item, from_status=prev.value, to_status="proof_sent", note=note)
    sync_review_status(db, order, actor=admin, background=background)
    background.add_task(notifications.notify_proof_sent, order.user.email, order.id, item.product.name, note)
    return proof


def customer_approve_proof(db: Session, order: Order, item: OrderItem, user: User, background: BackgroundTasks) -> None:
    _require_reviewable(order)
    if item.artwork_status != ArtworkStatus.proof_sent:
        raise OrderError("There is no proof awaiting your approval", 409)
    item.artwork_status = ArtworkStatus.approved
    record_event(db, order, "proof_approved", actor=user, item=item, from_status="proof_sent", to_status="approved")
    sync_review_status(db, order, actor=user, background=background)


def customer_request_changes(db: Session, order: Order, item: OrderItem, user: User, note: str) -> None:
    _require_reviewable(order)
    if item.artwork_status != ArtworkStatus.proof_sent:
        raise OrderError("There is no proof to request changes on", 409)
    item.artwork_status = ArtworkStatus.changes_requested
    item.review_note = note
    record_event(db, order, "proof_changes_requested", actor=user, item=item, from_status="proof_sent", to_status="changes_requested", note=note)
    sync_review_status(db, order, actor=user)


# ---------- production ----------

def start_production(db: Session, order: Order, admin: User, note: str | None) -> None:
    transition(db, order, OrderStatus.in_production, actor=admin, note=note, event_type="production_started")


def ship(db: Session, order: Order, admin: User, tracking: str | None, background: BackgroundTasks) -> None:
    order.tracking_number = tracking
    transition(db, order, OrderStatus.shipped, actor=admin, note=tracking, event_type="shipped")
    background.add_task(notifications.notify_order_shipped, order.user.email, order.id, tracking)


def complete(db: Session, order: Order, admin: User) -> None:
    transition(db, order, OrderStatus.completed, actor=admin, event_type="completed")


def reopen_review(db: Session, order: Order, admin: User, note: str | None) -> None:
    """Send an approved order back to review, e.g. a production issue was found before printing."""
    transition(db, order, OrderStatus.in_review, actor=admin, note=note, event_type="review_reopened")
