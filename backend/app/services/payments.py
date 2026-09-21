"""Payment providers. Stripe Checkout in production, a fake provider for development and tests."""

import json
import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

from app.core.config import get_settings
from app.models import Order, Payment


class PaymentError(RuntimeError):
    pass


@dataclass
class CheckoutResult:
    session_id: str
    url: str
    payment_intent_id: str | None = None


@dataclass
class WebhookEvent:
    kind: str  # "checkout_completed" | "ignored"
    session_id: str | None = None
    payment_intent_id: str | None = None


class PaymentProvider(Protocol):
    name: str

    def create_checkout(self, order: Order, amount_cents: int, currency: str, success_url: str, cancel_url: str, customer_email: str) -> CheckoutResult: ...
    def refund(self, payment: Payment, amount_cents: int) -> str: ...
    def parse_webhook(self, payload: bytes, signature: str | None) -> WebhookEvent: ...


class FakeProvider:
    name = "fake"

    def __init__(self, frontend_url: str):
        self.frontend_url = frontend_url.rstrip("/")

    def create_checkout(self, order, amount_cents, currency, success_url, cancel_url, customer_email):
        session_id = f"fake_cs_{uuid.uuid4().hex}"
        return CheckoutResult(session_id=session_id, url=f"{self.frontend_url}/fake-checkout/{session_id}")

    def refund(self, payment, amount_cents):
        return f"fake_re_{uuid.uuid4().hex}"

    def parse_webhook(self, payload, signature):
        try:
            body = json.loads(payload or b"{}")
        except json.JSONDecodeError as exc:
            raise PaymentError("Invalid webhook payload") from exc
        if body.get("type") == "checkout.session.completed":
            return WebhookEvent(kind="checkout_completed", session_id=body.get("session_id"), payment_intent_id=body.get("payment_intent_id"))
        return WebhookEvent(kind="ignored")


class StripeProvider:
    name = "stripe"

    def __init__(self, secret_key: str, webhook_secret: str | None):
        import stripe

        stripe.api_key = secret_key
        self.stripe = stripe
        self.webhook_secret = webhook_secret

    def create_checkout(self, order, amount_cents, currency, success_url, cancel_url, customer_email):
        try:
            session = self.stripe.checkout.Session.create(
                mode="payment",
                customer_email=customer_email,
                line_items=[
                    {
                        "quantity": 1,
                        "price_data": {
                            "currency": currency,
                            "unit_amount": amount_cents,
                            "product_data": {"name": f"Print order {order.id[:8]}"},
                        },
                    }
                ],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"order_id": order.id},
                payment_intent_data={"metadata": {"order_id": order.id}},
            )
        except self.stripe.error.StripeError as exc:
            raise PaymentError(str(exc)) from exc
        return CheckoutResult(session_id=session.id, url=session.url, payment_intent_id=session.payment_intent)

    def refund(self, payment, amount_cents):
        if not payment.payment_intent_id:
            raise PaymentError("Payment has no payment intent to refund")
        try:
            refund = self.stripe.Refund.create(payment_intent=payment.payment_intent_id, amount=amount_cents)
        except self.stripe.error.StripeError as exc:
            raise PaymentError(str(exc)) from exc
        return refund.id

    def parse_webhook(self, payload, signature):
        if not self.webhook_secret:
            raise PaymentError("STRIPE_WEBHOOK_SECRET is not configured")
        try:
            event = self.stripe.Webhook.construct_event(payload, signature or "", self.webhook_secret)
        except (ValueError, self.stripe.error.SignatureVerificationError) as exc:
            raise PaymentError("Invalid Stripe webhook signature") from exc
        if event["type"] == "checkout.session.completed":
            obj = event["data"]["object"]
            return WebhookEvent(kind="checkout_completed", session_id=obj["id"], payment_intent_id=obj.get("payment_intent"))
        return WebhookEvent(kind="ignored")


@lru_cache
def get_payment_provider() -> PaymentProvider:
    s = get_settings()
    if s.payment_provider == "stripe":
        if not s.stripe_secret_key:
            raise RuntimeError("STRIPE_SECRET_KEY must be set when PAYMENT_PROVIDER=stripe")
        return StripeProvider(s.stripe_secret_key, s.stripe_webhook_secret)
    if s.is_production:
        raise RuntimeError("The fake payment provider cannot be used in production")
    return FakeProvider(s.frontend_url)
