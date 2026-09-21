from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_any_order, item_of, load_order, require_admin
from app.api.routes.orders import serialize_order
from app.api.routes.products import get_product_by_slug
from app.db.session import get_db
from app.models import OptionChoice, OptionGroup, Order, OrderStatus, Product, QuantityTier, User
from app.schemas.catalog import ProductIn, ProductOut, ProductPatch
from app.schemas.orders import AdminOrderSummary, ArtworkOut, NoteIn, OrderOut, ReasonIn, ShipIn
from app.services import orders as order_service
from app.services.artwork import ArtworkError
from app.services.orders import OrderError
from app.services.payments import PaymentError

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _raise(exc: Exception):
    if isinstance(exc, OrderError):
        raise HTTPException(exc.status_code, str(exc)) from exc
    if isinstance(exc, ArtworkError):
        raise HTTPException(422, str(exc)) from exc
    if isinstance(exc, PaymentError):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Payment provider error: {exc}") from exc
    raise exc


def _commit_and_return(db: Session, order: Order) -> OrderOut:
    db.commit()
    return serialize_order(load_order(db, order.id))


# ---------- orders ----------

@router.get("/orders", response_model=list[AdminOrderSummary])
def list_orders(status_filter: OrderStatus | None = None, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    q = db.query(Order).options(joinedload(Order.user)).filter(Order.status != OrderStatus.cart)
    if status_filter:
        q = q.filter(Order.status == status_filter)
    orders = q.order_by(Order.placed_at.desc().nullslast(), Order.created_at.desc()).offset(offset).limit(min(limit, 200)).all()
    out = []
    for o in orders:
        s = AdminOrderSummary.model_validate(o, from_attributes=True)
        s.item_count = len(o.items)
        s.customer_email = o.user.email
        out.append(s)
    return out


@router.get("/orders/review-queue", response_model=list[AdminOrderSummary])
def review_queue(db: Session = Depends(get_db)):
    """Paid orders with artwork waiting on the shop, oldest first."""
    orders = (
        db.query(Order)
        .options(joinedload(Order.user))
        .filter(Order.status.in_([OrderStatus.paid, OrderStatus.in_review]))
        .order_by(Order.placed_at.asc())
        .all()
    )
    out = []
    for o in orders:
        s = AdminOrderSummary.model_validate(o, from_attributes=True)
        s.item_count = len(o.items)
        s.customer_email = o.user.email
        out.append(s)
    return out


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order: Order = Depends(get_any_order)):
    return serialize_order(order)


@router.post("/orders/{order_id}/items/{item_id}/approve", response_model=OrderOut)
def approve_item(item_id: str, body: NoteIn, background: BackgroundTasks, order: Order = Depends(get_any_order),
                 admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = item_of(order, item_id)
    try:
        order_service.approve_artwork(db, order, item, admin, body.note, background)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    return _commit_and_return(db, order)


@router.post("/orders/{order_id}/items/{item_id}/reject", response_model=OrderOut)
def reject_item(item_id: str, body: ReasonIn, background: BackgroundTasks, order: Order = Depends(get_any_order),
                admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = item_of(order, item_id)
    try:
        order_service.reject_artwork(db, order, item, admin, body.reason, background)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    return _commit_and_return(db, order)


@router.post("/orders/{order_id}/items/{item_id}/proof", response_model=ArtworkOut, status_code=status.HTTP_201_CREATED)
async def send_proof(item_id: str, background: BackgroundTasks, file: UploadFile = File(...), note: str | None = Form(default=None),
                     order: Order = Depends(get_any_order), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    item = item_of(order, item_id)
    data = await file.read()
    try:
        proof = order_service.send_proof(db, order, item, admin, data, file.filename or "proof.pdf", note, background)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    db.commit()
    return ArtworkOut.model_validate(proof, from_attributes=True).model_copy(update={"has_preview": proof.preview_key is not None})


@router.post("/orders/{order_id}/production", response_model=OrderOut)
def start_production(body: NoteIn, order: Order = Depends(get_any_order), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        order_service.start_production(db, order, admin, body.note)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    return _commit_and_return(db, order)


@router.post("/orders/{order_id}/ship", response_model=OrderOut)
def ship(body: ShipIn, background: BackgroundTasks, order: Order = Depends(get_any_order), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        order_service.ship(db, order, admin, body.tracking_number, background)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    return _commit_and_return(db, order)


@router.post("/orders/{order_id}/complete", response_model=OrderOut)
def complete(order: Order = Depends(get_any_order), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        order_service.complete(db, order, admin)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    return _commit_and_return(db, order)


@router.post("/orders/{order_id}/reopen-review", response_model=OrderOut)
def reopen_review(body: NoteIn, order: Order = Depends(get_any_order), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        order_service.reopen_review(db, order, admin, body.note)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    return _commit_and_return(db, order)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_or_refund(body: NoteIn, background: BackgroundTasks, order: Order = Depends(get_any_order), admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Cancels an unpaid order, or refunds a paid one in full through the payment provider."""
    try:
        order_service.cancel_or_refund(db, order, admin, body.note, background)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    return _commit_and_return(db, order)


# ---------- catalog ----------

@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(body: ProductIn, db: Session = Depends(get_db)):
    if db.query(Product).filter(Product.slug == body.slug).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug already exists")
    product = Product(slug=body.slug, name=body.name, category=body.category, description=body.description,
                      active=body.active, pricing_config=body.pricing_config)
    for gi, g in enumerate(body.option_groups):
        group = OptionGroup(key=g.key, name=g.name, required=g.required, sort_order=gi)
        for ci, c in enumerate(g.choices):
            group.choices.append(OptionChoice(key=c.key, name=c.name, price_type=c.price_type, price_value=c.price_value,
                                              is_default=c.is_default, sort_order=ci))
        product.option_groups.append(group)
    for t in body.quantity_tiers:
        product.quantity_tiers.append(QuantityTier(min_quantity=t.min_quantity, discount_pct=t.discount_pct))
    db.add(product)
    db.commit()
    return get_product_by_slug(db, product.slug, include_inactive=True)


@router.patch("/products/{slug}", response_model=ProductOut)
def patch_product(slug: str, body: ProductPatch, db: Session = Depends(get_db)):
    product = get_product_by_slug(db, slug, include_inactive=True)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    return get_product_by_slug(db, slug, include_inactive=True)
