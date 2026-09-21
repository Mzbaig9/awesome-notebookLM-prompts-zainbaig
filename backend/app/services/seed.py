"""Starter catalog modelled on a custom signage shop: table runners, banners, flags, posters."""

from sqlalchemy.orm import Session

from app.models import OptionChoice, OptionGroup, PriceType, Product, QuantityTier

M, F, SQ, U = PriceType.multiplier, PriceType.flat, PriceType.per_sqft, PriceType.per_unit

CATALOG = [
    {
        "slug": "table-runner",
        "name": "Custom Table Runner",
        "category": "table-covers",
        "description": "Full colour dye sublimated polyester table runner, machine washable.",
        "pricing_config": {
            "mode": "unit",
            "base_cents": 4900,
            "min_cents": 4900,
            "size": {
                "presets": [
                    {"key": "2x5.7", "label": "2 ft x 5.7 ft (6 ft table)", "width_in": 24, "height_in": 68},
                    {"key": "2x7.7", "label": "2 ft x 7.7 ft (8 ft table)", "width_in": 24, "height_in": 92},
                    {"key": "3x5.7", "label": "3 ft x 5.7 ft (6 ft table)", "width_in": 36, "height_in": 68},
                ]
            },
            "allowed_file_types": ["pdf", "ai", "eps", "png", "jpg", "jpeg", "tif", "tiff", "psd"],
            "min_dpi": 100,
            "bleed_in": 0.5,
        },
        "groups": [
            ("material", "Material", [("polyester", "Polyester", M, 1.0, True), ("stretch", "Stretch fabric", M, 1.25, False)]),
            ("print_sides", "Print sides", [("single", "Single sided", M, 1.0, True), ("double", "Double sided", M, 1.6, False)]),
            ("finishing", "Finishing", [("hemmed", "Hemmed edges", F, 0, True), ("open", "Open edges", F, -300, False)]),
            ("turnaround", "Turnaround", [("standard", "Standard (5 business days)", M, 1.0, True), ("rush", "Rush (2 business days)", M, 1.3, False)]),
        ],
        "tiers": [(2, 5), (5, 10), (10, 15), (25, 20)],
    },
    {
        "slug": "vinyl-banner",
        "name": "Vinyl Banner",
        "category": "banners",
        "description": "Weather resistant vinyl banner, any custom size, hemmed with grommets.",
        "pricing_config": {
            "mode": "area",
            "base_cents_per_sqft": 350,
            "min_cents": 1500,
            "size": {
                "presets": [
                    {"key": "2x4", "label": "2 ft x 4 ft", "width_in": 24, "height_in": 48},
                    {"key": "3x6", "label": "3 ft x 6 ft", "width_in": 36, "height_in": 72},
                    {"key": "4x8", "label": "4 ft x 8 ft", "width_in": 48, "height_in": 96},
                ],
                "custom": {"min_w": 12, "max_w": 600, "min_h": 12, "max_h": 120},
            },
            "allowed_file_types": ["pdf", "ai", "eps", "png", "jpg", "jpeg", "tif", "tiff"],
            "min_dpi": 72,
            "bleed_in": 0.25,
        },
        "groups": [
            ("material", "Material", [("13oz", "13 oz matte vinyl", M, 1.0, True), ("18oz", "18 oz blockout vinyl", M, 1.4, False), ("mesh", "Mesh vinyl (wind resistant)", M, 1.3, False)]),
            ("print_sides", "Print sides", [("single", "Single sided", M, 1.0, True), ("double", "Double sided", M, 1.8, False)]),
            ("hem", "Hem", [("hemmed", "Hemmed", F, 0, True), ("none", "No hem", F, 0, False)]),
            ("grommets", "Grommets", [("every_2ft", "Every 2 ft", F, 0, True), ("corners", "Corners only", F, 0, False), ("none", "No grommets", F, 0, False)]),
            ("pole_pockets", "Pole pockets", [("none", "None", F, 0, True), ("top_bottom", "Top and bottom", SQ, 75, False)]),
            ("turnaround", "Turnaround", [("standard", "Standard (5 business days)", M, 1.0, True), ("rush", "Rush (2 business days)", M, 1.3, False)]),
        ],
        "tiers": [(2, 5), (5, 10), (10, 15), (25, 22)],
    },
    {
        "slug": "retractable-banner",
        "name": "Retractable Banner Stand",
        "category": "displays",
        "description": "Roll up banner stand with printed graphic and carrying case.",
        "pricing_config": {
            "mode": "unit",
            "base_cents": 9900,
            "min_cents": 9900,
            "size": {
                "presets": [
                    {"key": "33x81", "label": "33 in x 81 in", "width_in": 33, "height_in": 81},
                    {"key": "47x81", "label": "47 in x 81 in", "width_in": 47, "height_in": 81},
                ]
            },
            "allowed_file_types": ["pdf", "ai", "eps", "png", "jpg", "jpeg", "tif", "tiff"],
            "min_dpi": 100,
            "bleed_in": 0.25,
        },
        "groups": [
            ("stand", "Stand", [("economy", "Economy stand", M, 1.0, True), ("premium", "Premium stand", M, 1.5, False)]),
            ("material", "Graphic material", [("vinyl", "Vinyl", M, 1.0, True), ("fabric", "Fabric", M, 1.2, False)]),
            ("case", "Carrying case", [("included", "Standard bag", F, 0, True), ("hard", "Hard case", U, 2500, False)]),
            ("turnaround", "Turnaround", [("standard", "Standard (5 business days)", M, 1.0, True), ("rush", "Rush (2 business days)", M, 1.3, False)]),
        ],
        "tiers": [(2, 5), (5, 10), (10, 15)],
    },
    {
        "slug": "poster",
        "name": "Poster",
        "category": "posters",
        "description": "High resolution poster print on photo paper or coated paper.",
        "pricing_config": {
            "mode": "area",
            "base_cents_per_sqft": 900,
            "min_cents": 1200,
            "size": {
                "presets": [
                    {"key": "18x24", "label": "18 in x 24 in", "width_in": 18, "height_in": 24},
                    {"key": "24x36", "label": "24 in x 36 in", "width_in": 24, "height_in": 36},
                ],
                "custom": {"min_w": 8, "max_w": 60, "min_h": 8, "max_h": 120},
            },
            "allowed_file_types": ["pdf", "png", "jpg", "jpeg", "tif", "tiff"],
            "min_dpi": 150,
            "bleed_in": 0.125,
        },
        "groups": [
            ("paper", "Paper", [("photo_gloss", "Photo paper gloss", M, 1.0, True), ("photo_matte", "Photo paper matte", M, 1.0, False), ("coated", "Coated paper", M, 0.8, False)]),
            ("lamination", "Lamination", [("none", "None", F, 0, True), ("gloss", "Gloss laminate", SQ, 250, False), ("matte", "Matte laminate", SQ, 250, False)]),
            ("turnaround", "Turnaround", [("standard", "Standard (3 business days)", M, 1.0, True), ("rush", "Next day", M, 1.4, False)]),
        ],
        "tiers": [(5, 10), (10, 15), (25, 20), (50, 25)],
    },
]


def seed_catalog(db: Session) -> int:
    created = 0
    for spec in CATALOG:
        if db.query(Product).filter(Product.slug == spec["slug"]).first():
            continue
        product = Product(slug=spec["slug"], name=spec["name"], category=spec["category"],
                          description=spec["description"], pricing_config=spec["pricing_config"])
        for gi, (gkey, gname, choices) in enumerate(spec["groups"]):
            group = OptionGroup(key=gkey, name=gname, sort_order=gi)
            for ci, (ckey, cname, ptype, pval, default) in enumerate(choices):
                group.choices.append(OptionChoice(key=ckey, name=cname, price_type=ptype, price_value=pval, is_default=default, sort_order=ci))
            product.option_groups.append(group)
        for min_q, pct in spec["tiers"]:
            product.quantity_tiers.append(QuantityTier(min_quantity=min_q, discount_pct=pct))
        db.add(product)
        created += 1
    db.commit()
    return created
