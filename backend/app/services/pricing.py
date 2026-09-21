"""Server side price computation. The client never sets a price; it only sends a configuration."""

from dataclasses import dataclass, field

from app.models import PriceType, Product


class PricingError(ValueError):
    pass


@dataclass
class Quote:
    unit_price_cents: int
    line_total_cents: int
    quantity: int
    width_in: float | None
    height_in: float | None
    size_preset: str | None
    resolved_options: dict[str, str]
    breakdown: dict = field(default_factory=dict)


def _resolve_size(product: Product, width_in, height_in, size_preset):
    size_cfg = (product.pricing_config or {}).get("size")
    if not size_cfg:
        return None, None, None
    presets = {p["key"]: p for p in size_cfg.get("presets", [])}
    if size_preset:
        preset = presets.get(size_preset)
        if not preset:
            raise PricingError(f"Unknown size preset '{size_preset}'")
        return float(preset["width_in"]), float(preset["height_in"]), size_preset
    custom = size_cfg.get("custom")
    if not custom:
        raise PricingError("This product requires a size preset")
    if width_in is None or height_in is None:
        raise PricingError("width_in and height_in are required for a custom size")
    if not (custom["min_w"] <= width_in <= custom["max_w"]) or not (custom["min_h"] <= height_in <= custom["max_h"]):
        raise PricingError(
            f"Custom size must be between {custom['min_w']}x{custom['min_h']} and {custom['max_w']}x{custom['max_h']} inches"
        )
    return float(width_in), float(height_in), None


def quote_item(
    product: Product,
    quantity: int,
    width_in: float | None = None,
    height_in: float | None = None,
    size_preset: str | None = None,
    selected_options: dict[str, str] | None = None,
) -> Quote:
    if not product.active:
        raise PricingError("Product is not available")
    if quantity < 1:
        raise PricingError("Quantity must be at least 1")
    selected_options = selected_options or {}
    cfg = product.pricing_config or {}

    w, h, preset = _resolve_size(product, width_in, height_in, size_preset)
    sqft = (w * h) / 144.0 if w and h else 0.0

    mode = cfg.get("mode", "unit")
    if mode == "area":
        base = float(cfg.get("base_cents_per_sqft", 0)) * sqft
    else:
        base = float(cfg.get("base_cents", 0))

    multiplier = 1.0
    flat = 0.0
    per_sqft = 0.0
    per_unit = 0.0
    resolved: dict[str, str] = {}
    option_lines: list[dict] = []

    for group in product.option_groups:
        choice_key = selected_options.get(group.key)
        choice = None
        if choice_key is not None:
            choice = next((c for c in group.choices if c.key == choice_key), None)
            if choice is None:
                raise PricingError(f"Unknown choice '{choice_key}' for option '{group.key}'")
        else:
            choice = next((c for c in group.choices if c.is_default), None)
            if choice is None and group.required:
                raise PricingError(f"Option '{group.key}' is required")
        if choice is None:
            continue
        resolved[group.key] = choice.key
        if choice.price_type == PriceType.multiplier:
            multiplier *= choice.price_value
        elif choice.price_type == PriceType.flat:
            flat += choice.price_value
        elif choice.price_type == PriceType.per_sqft:
            per_sqft += choice.price_value
        elif choice.price_type == PriceType.per_unit:
            per_unit += choice.price_value
        option_lines.append(
            {"group": group.key, "choice": choice.key, "price_type": choice.price_type.value, "value": choice.price_value}
        )

    unknown = set(selected_options) - {g.key for g in product.option_groups}
    if unknown:
        raise PricingError(f"Unknown options: {', '.join(sorted(unknown))}")

    unit = (base + per_sqft * sqft + per_unit) * multiplier + flat
    unit = max(unit, float(cfg.get("min_cents", 0)))

    discount_pct = 0.0
    for tier in product.quantity_tiers:
        if quantity >= tier.min_quantity:
            discount_pct = max(discount_pct, tier.discount_pct)
    unit_after = unit * (1 - discount_pct / 100.0)

    unit_cents = int(round(unit_after))
    line_total = unit_cents * quantity

    return Quote(
        unit_price_cents=unit_cents,
        line_total_cents=line_total,
        quantity=quantity,
        width_in=w,
        height_in=h,
        size_preset=preset,
        resolved_options=resolved,
        breakdown={
            "mode": mode,
            "sqft": round(sqft, 3),
            "base_cents": round(base, 2),
            "options": option_lines,
            "multiplier": round(multiplier, 4),
            "flat_cents": flat,
            "unit_before_discount_cents": round(unit, 2),
            "quantity_discount_pct": discount_pct,
        },
    )
