from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PriceType


class OptionChoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    name: str
    price_type: PriceType
    price_value: float
    is_default: bool


class OptionGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    name: str
    required: bool
    choices: list[OptionChoiceOut]


class QuantityTierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    min_quantity: int
    discount_pct: float


class ProductSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    slug: str
    name: str
    category: str
    description: str | None
    active: bool


class ProductOut(ProductSummary):
    pricing_config: dict
    option_groups: list[OptionGroupOut]
    quantity_tiers: list[QuantityTierOut]


class QuoteIn(BaseModel):
    quantity: int = Field(ge=1, le=100000)
    width_in: float | None = Field(default=None, gt=0)
    height_in: float | None = Field(default=None, gt=0)
    size_preset: str | None = None
    options: dict[str, str] = Field(default_factory=dict)


class QuoteOut(BaseModel):
    unit_price_cents: int
    line_total_cents: int
    quantity: int
    width_in: float | None
    height_in: float | None
    size_preset: str | None
    resolved_options: dict[str, str]
    breakdown: dict
    currency: str


class OptionChoiceIn(BaseModel):
    key: str
    name: str
    price_type: PriceType = PriceType.multiplier
    price_value: float = 1.0
    is_default: bool = False


class OptionGroupIn(BaseModel):
    key: str
    name: str
    required: bool = True
    choices: list[OptionChoiceIn]


class QuantityTierIn(BaseModel):
    min_quantity: int = Field(ge=1)
    discount_pct: float = Field(ge=0, le=100)


class ProductIn(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=120)
    name: str
    category: str
    description: str | None = None
    active: bool = True
    pricing_config: dict
    option_groups: list[OptionGroupIn] = Field(default_factory=list)
    quantity_tiers: list[QuantityTierIn] = Field(default_factory=list)


class ProductPatch(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    active: bool | None = None
    pricing_config: dict | None = None
