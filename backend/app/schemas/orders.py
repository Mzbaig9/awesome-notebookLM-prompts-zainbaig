from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ArtworkKind, ArtworkStatus, DesignService, OrderStatus, PaymentStatus
from app.schemas.catalog import ProductSummary


class CartItemIn(BaseModel):
    product_slug: str
    quantity: int = Field(ge=1, le=100000)
    width_in: float | None = Field(default=None, gt=0)
    height_in: float | None = Field(default=None, gt=0)
    size_preset: str | None = None
    options: dict[str, str] = Field(default_factory=dict)
    design_service: DesignService = DesignService.upload
    instructions: str | None = Field(default=None, max_length=2000)


class CartItemPatch(BaseModel):
    quantity: int | None = Field(default=None, ge=1, le=100000)
    width_in: float | None = Field(default=None, gt=0)
    height_in: float | None = Field(default=None, gt=0)
    size_preset: str | None = None
    options: dict[str, str] | None = None
    design_service: DesignService | None = None
    instructions: str | None = Field(default=None, max_length=2000)


class ShippingAddress(BaseModel):
    name: str
    line1: str
    line2: str | None = None
    city: str
    region: str
    postal_code: str
    country: str = Field(min_length=2, max_length=2)
    phone: str | None = None


class CheckoutIn(BaseModel):
    shipping_method: str = Field(pattern=r"^(standard|express)$")
    shipping_address: ShippingAddress
    note: str | None = Field(default=None, max_length=2000)


class CheckoutOut(BaseModel):
    order_id: str
    payment_id: str
    checkout_url: str
    total_cents: int
    currency: str


class ArtworkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    kind: ArtworkKind
    version: int
    original_filename: str
    content_type: str
    size_bytes: int
    file_metadata: dict
    warnings: list
    note: str | None
    has_preview: bool = False
    created_at: datetime


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product: ProductSummary
    quantity: int
    width_in: float | None
    height_in: float | None
    size_preset: str | None
    selected_options: dict
    design_service: DesignService
    unit_price_cents: int
    line_total_cents: int
    price_breakdown: dict
    artwork_status: ArtworkStatus
    review_note: str | None
    customer_instructions: str | None
    artworks: list[ArtworkOut]


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    provider: str
    status: PaymentStatus
    amount_cents: int
    currency: str
    checkout_url: str | None
    refund_id: str | None
    created_at: datetime


class OrderEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    item_id: str | None
    actor_id: str | None
    event_type: str
    from_status: str | None
    to_status: str | None
    note: str | None
    created_at: datetime


class OrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: OrderStatus
    currency: str
    subtotal_cents: int
    shipping_cents: int
    total_cents: int
    item_count: int = 0
    placed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class OrderOut(OrderSummary):
    user_id: str
    shipping_method: str | None
    shipping_address: dict | None
    customer_note: str | None
    tracking_number: str | None
    items: list[OrderItemOut]
    payments: list[PaymentOut]
    events: list[OrderEventOut]


class AdminOrderSummary(OrderSummary):
    user_id: str
    customer_email: str | None = None


class NoteIn(BaseModel):
    note: str | None = Field(default=None, max_length=2000)


class ReasonIn(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


class ShipIn(BaseModel):
    tracking_number: str | None = Field(default=None, max_length=120)
