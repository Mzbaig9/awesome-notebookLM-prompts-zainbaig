from sqlalchemy import JSON, Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.common import IdMixin, TimestampMixin
from app.models.enums import PriceType


class Product(IdMixin, TimestampMixin, Base):
    """A configurable print product, e.g. Table Runner, Vinyl Banner.

    pricing_config keys:
      mode: "area" (price scales with width x height) or "unit" (fixed per piece)
      base_cents_per_sqft: used in area mode
      base_cents: used in unit mode
      min_cents: floor per unit
      size: {"presets": [{"key","label","width_in","height_in"}], "custom": {"min_w","max_w","min_h","max_h"}} or null
      allowed_file_types: list of extensions
      min_dpi: minimum effective DPI for raster artwork
      bleed_in: bleed expected around the artwork
    """

    __tablename__ = "products"

    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pricing_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    option_groups = relationship(
        "OptionGroup", back_populates="product", cascade="all, delete-orphan", order_by="OptionGroup.sort_order"
    )
    quantity_tiers = relationship(
        "QuantityTier", back_populates="product", cascade="all, delete-orphan", order_by="QuantityTier.min_quantity"
    )


class OptionGroup(IdMixin, Base):
    __tablename__ = "option_groups"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product = relationship("Product", back_populates="option_groups")
    choices = relationship(
        "OptionChoice", back_populates="group", cascade="all, delete-orphan", order_by="OptionChoice.sort_order"
    )


class OptionChoice(IdMixin, Base):
    __tablename__ = "option_choices"

    group_id: Mapped[str] = mapped_column(ForeignKey("option_groups.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    price_type: Mapped[PriceType] = mapped_column(Enum(PriceType), default=PriceType.multiplier, nullable=False)
    price_value: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    group = relationship("OptionGroup", back_populates="choices")


class QuantityTier(IdMixin, Base):
    __tablename__ = "quantity_tiers"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    min_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_pct: Mapped[float] = mapped_column(Float, nullable=False)

    product = relationship("Product", back_populates="quantity_tiers")
