from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, item_of, load_order
from app.api.routes.products import get_product_by_slug
from app.db.session import get_db
from app.models import User
from app.schemas.orders import ArtworkOut, CartItemIn, CartItemPatch, CheckoutIn, CheckoutOut, OrderOut
from app.services import orders as order_service
from app.services.artwork import ArtworkError
from app.services.orders import OrderError
from app.services.payments import PaymentError
from app.services.pricing import PricingError
from app.api.routes.orders import serialize_order

router = APIRouter(prefix="/cart", tags=["cart"])


def _raise(exc: Exception):
    if isinstance(exc, OrderError):
        raise HTTPException(exc.status_code, str(exc)) from exc
    if isinstance(exc, (PricingError, ArtworkError)):
        raise HTTPException(422, str(exc)) from exc
    if isinstance(exc, PaymentError):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Payment provider error: {exc}") from exc
    raise exc


def _cart(db: Session, user: User):
    cart = order_service.get_or_create_cart(db, user)
    return load_order(db, cart.id)


@router.get("", response_model=OrderOut)
def get_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = _cart(db, user)
    db.commit()
    return serialize_order(cart)


@router.post("/items", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def add_item(body: CartItemIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = _cart(db, user)
    product = get_product_by_slug(db, body.product_slug)
    try:
        order_service.add_item(db, cart, product, body.quantity, body.width_in, body.height_in, body.size_preset,
                               body.options, body.design_service, body.instructions)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    db.commit()
    return serialize_order(load_order(db, cart.id))


@router.patch("/items/{item_id}", response_model=OrderOut)
def update_item(item_id: str, body: CartItemPatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = _cart(db, user)
    item = item_of(cart, item_id)
    try:
        order_service.update_item(db, cart, item, body.quantity, body.width_in, body.height_in, body.size_preset,
                                  body.options, body.design_service, body.instructions)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    db.commit()
    return serialize_order(load_order(db, cart.id))


@router.delete("/items/{item_id}", response_model=OrderOut)
def remove_item(item_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = _cart(db, user)
    item = item_of(cart, item_id)
    try:
        order_service.remove_item(db, cart, item)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    db.commit()
    return serialize_order(load_order(db, cart.id))


@router.post("/items/{item_id}/artwork", response_model=ArtworkOut, status_code=status.HTTP_201_CREATED)
async def upload_artwork(item_id: str, file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = _cart(db, user)
    item = item_of(cart, item_id)
    data = await file.read()
    try:
        art = order_service.customer_upload(db, cart, item, data, file.filename or "artwork", user)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    db.commit()
    return ArtworkOut.model_validate(art, from_attributes=True).model_copy(update={"has_preview": art.preview_key is not None})


@router.post("/checkout", response_model=CheckoutOut)
def checkout(body: CheckoutIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = _cart(db, user)
    try:
        payment = order_service.checkout(db, cart, user, body.shipping_method, body.shipping_address.model_dump(), body.note)
    except Exception as exc:
        db.rollback()
        _raise(exc)
    db.commit()
    return CheckoutOut(order_id=cart.id, payment_id=payment.id, checkout_url=payment.checkout_url or "",
                       total_cents=cart.total_cents, currency=cart.currency)
