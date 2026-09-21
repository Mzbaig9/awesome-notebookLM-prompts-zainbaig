from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import IdMixin, TimestampMixin, utcnow
from app.models.enums import ArtworkKind, ArtworkStatus, DesignService, OrderStatus, PaymentStatus


class Order(IdMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.cart, index=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="cad", nullable=False)
    subtotal_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shipping_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shipping_method: Mapped[str | None] = mapped_column(String(40))
    shipping_address: Mapped[dict | None] = mapped_column(JSON)
    customer_note: Mapped[str | None] = mapped_column(Text)
    tracking_number: Mapped[str | None] = mapped_column(String(120))
    placed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", order_by="OrderItem.created_at")
    events = relationship("OrderEvent", back_populates="order", cascade="all, delete-orphan", order_by="OrderEvent.created_at")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan", order_by="Payment.created_at")


class OrderItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    width_in: Mapped[float | None] = mapped_column(Float)
    height_in: Mapped[float | None] = mapped_column(Float)
    size_preset: Mapped[str | None] = mapped_column(String(80))
    selected_options: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    design_service: Mapped[DesignService] = mapped_column(
        Enum(DesignService), default=DesignService.upload, nullable=False
    )
    unit_price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    line_total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price_breakdown: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    artwork_status: Mapped[ArtworkStatus] = mapped_column(
        Enum(ArtworkStatus), default=ArtworkStatus.awaiting_artwork, nullable=False
    )
    review_note: Mapped[str | None] = mapped_column(Text)
    customer_instructions: Mapped[str | None] = mapped_column(Text)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    artworks = relationship(
        "Artwork", back_populates="item", cascade="all, delete-orphan", order_by="Artwork.created_at"
    )


class Artwork(IdMixin, Base):
    __tablename__ = "artworks"

    item_id: Mapped[str] = mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"), index=True, nullable=False)
    kind: Mapped[ArtworkKind] = mapped_column(Enum(ArtworkKind), default=ArtworkKind.customer_upload, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    preview_key: Mapped[str | None] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    warnings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    uploaded_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    item = relationship("OrderItem", back_populates="artworks")


class OrderEvent(IdMixin, Base):
    __tablename__ = "order_events"

    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    item_id: Mapped[str | None] = mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"))
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(40))
    to_status: Mapped[str | None] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    order = relationship("Order", back_populates="events")


class Payment(IdMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    checkout_session_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    payment_intent_id: Mapped[str | None] = mapped_column(String(255), index=True)
    checkout_url: Mapped[str | None] = mapped_column(String(1000))
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.pending, nullable=False)
    refund_id: Mapped[str | None] = mapped_column(String(255))
    refunded_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    order = relationship("Order", back_populates="payments")
