"""Customer emails. Console backend logs them; SMTP backend sends them. Called from background tasks."""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

log = logging.getLogger("printshop.email")


def send_email(to: str, subject: str, body: str) -> None:
    s = get_settings()
    if s.email_backend == "smtp" and s.smtp_host:
        msg = EmailMessage()
        msg["From"] = s.email_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15) as smtp:
                smtp.starttls()
                if s.smtp_user:
                    smtp.login(s.smtp_user, s.smtp_password or "")
                smtp.send_message(msg)
        except Exception:  # never let email failures break an order flow
            log.exception("Failed to send email to %s", to)
        return
    log.info("EMAIL to=%s subject=%r\n%s", to, subject, body)


def order_link(order_id: str) -> str:
    return f"{get_settings().frontend_url.rstrip('/')}/orders/{order_id}"


def notify_order_paid(to: str, order_id: str, total_cents: int, currency: str) -> None:
    send_email(
        to,
        f"Order {order_id[:8]} received",
        f"Thanks, we received your payment of {total_cents / 100:.2f} {currency.upper()}.\n"
        f"Our team will now review your artwork. Track it here: {order_link(order_id)}",
    )


def notify_artwork_rejected(to: str, order_id: str, product_name: str, reason: str) -> None:
    send_email(
        to,
        f"Action needed on order {order_id[:8]}",
        f"The artwork for '{product_name}' needs a fix before we can print it:\n\n{reason}\n\n"
        f"Upload a corrected file here: {order_link(order_id)}",
    )


def notify_proof_sent(to: str, order_id: str, product_name: str, note: str | None) -> None:
    send_email(
        to,
        f"Proof ready for order {order_id[:8]}",
        f"A digital proof for '{product_name}' is ready for your approval.\n"
        + (f"Note from our team: {note}\n" if note else "")
        + f"Review and approve it here: {order_link(order_id)}",
    )


def notify_order_approved(to: str, order_id: str) -> None:
    send_email(to, f"Order {order_id[:8]} approved", f"All artwork is approved and your order is heading to production.\n{order_link(order_id)}")


def notify_order_shipped(to: str, order_id: str, tracking: str | None) -> None:
    send_email(
        to,
        f"Order {order_id[:8]} shipped",
        f"Your order is on its way." + (f" Tracking: {tracking}" if tracking else "") + f"\n{order_link(order_id)}",
    )


def notify_order_refunded(to: str, order_id: str, amount_cents: int, currency: str, reason: str | None) -> None:
    send_email(
        to,
        f"Order {order_id[:8]} refunded",
        f"We refunded {amount_cents / 100:.2f} {currency.upper()} for this order."
        + (f"\nReason: {reason}" if reason else "")
        + f"\n{order_link(order_id)}",
    )
