from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Payment, User
from app.schemas.orders import OrderOut
from app.services import orders as order_service
from app.services.payments import PaymentError, get_payment_provider
from app.api.deps import load_order
from app.api.routes.orders import serialize_order

router = APIRouter(tags=["payments"])


@router.post("/webhooks/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    """Stripe calls this after checkout. Signature is verified by the provider. Safe to receive twice."""
    payload = await request.body()
    provider = get_payment_provider()
    try:
        event = provider.parse_webhook(payload, request.headers.get("stripe-signature"))
    except PaymentError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    if event.kind != "checkout_completed" or not event.session_id:
        return {"received": True, "handled": False}
    payment = db.query(Payment).filter(Payment.checkout_session_id == event.session_id).first()
    if payment is None:
        # unknown session: acknowledge so Stripe stops retrying, but do not fail
        return {"received": True, "handled": False}
    order_service.confirm_payment(db, payment, event.payment_intent_id, background)
    db.commit()
    return {"received": True, "handled": True}


@router.post("/payments/{payment_id}/simulate", response_model=OrderOut)
def simulate_payment(payment_id: str, background: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Development only: marks a fake checkout as paid, as the Stripe webhook would."""
    s = get_settings()
    if s.payment_provider != "fake" or s.is_production:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    payment = db.get(Payment, payment_id)
    if payment is None or payment.order.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment not found")
    order_service.confirm_payment(db, payment, f"fake_pi_{payment.id[:8]}", background)
    db.commit()
    return serialize_order(load_order(db, payment.order_id))
