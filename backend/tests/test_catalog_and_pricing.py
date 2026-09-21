def test_list_and_get_product(client):
    r = client.get("/products")
    assert r.status_code == 200
    slugs = {p["slug"] for p in r.json()}
    assert {"table-runner", "vinyl-banner", "retractable-banner", "poster"} <= slugs
    r = client.get("/products/vinyl-banner")
    assert r.status_code == 200
    body = r.json()
    assert [g["key"] for g in body["option_groups"]][:2] == ["material", "print_sides"]
    assert body["pricing_config"]["size"]["custom"]["max_w"] == 600


def test_quote_area_product_defaults(client):
    r = client.post("/products/vinyl-banner/quote", json={"quantity": 1, "size_preset": "3x6"})
    assert r.status_code == 200, r.text
    q = r.json()
    # 3x6 ft = 18 sqft * 350 = 6300 cents, all default options are neutral
    assert q["unit_price_cents"] == 6300
    assert q["line_total_cents"] == 6300
    assert q["resolved_options"]["material"] == "13oz"


def test_quote_applies_options_and_tiers(client):
    r = client.post(
        "/products/vinyl-banner/quote",
        json={"quantity": 10, "width_in": 48, "height_in": 24,
              "options": {"material": "18oz", "print_sides": "double", "pole_pockets": "top_bottom"}},
    )
    assert r.status_code == 200, r.text
    q = r.json()
    # 8 sqft: (350*8 + 75*8) * 1.4 * 1.8 = 8568 ; 10+ qty => 15% off => 7283
    assert q["unit_price_cents"] == 7283
    assert q["line_total_cents"] == 72830
    assert q["breakdown"]["quantity_discount_pct"] == 15


def test_quote_min_price_floor(client):
    r = client.post("/products/vinyl-banner/quote", json={"quantity": 1, "width_in": 12, "height_in": 12})
    assert r.status_code == 200
    assert r.json()["unit_price_cents"] == 1500


def test_quote_rejects_bad_config(client):
    r = client.post("/products/table-runner/quote", json={"quantity": 1})
    assert r.status_code == 422
    r = client.post("/products/table-runner/quote", json={"quantity": 1, "size_preset": "2x5.7", "options": {"material": "gold"}})
    assert r.status_code == 422
    r = client.post("/products/vinyl-banner/quote", json={"quantity": 1, "width_in": 5000, "height_in": 10})
    assert r.status_code == 422


def test_admin_can_create_product_and_customer_cannot(client, admin, customer):
    body = {
        "slug": "feather-flag", "name": "Feather Flag", "category": "flags",
        "pricing_config": {"mode": "unit", "base_cents": 7900, "min_cents": 7900},
        "option_groups": [{"key": "size", "name": "Size", "choices": [
            {"key": "small", "name": "Small", "price_type": "multiplier", "price_value": 1.0, "is_default": True},
            {"key": "large", "name": "Large", "price_type": "multiplier", "price_value": 1.5}]}],
        "quantity_tiers": [{"min_quantity": 3, "discount_pct": 10}],
    }
    assert client.post("/admin/products", json=body, headers=customer).status_code == 403
    r = client.post("/admin/products", json=body, headers=admin)
    assert r.status_code == 201, r.text
    r = client.post("/products/feather-flag/quote", json={"quantity": 3, "options": {"size": "large"}})
    assert r.json()["unit_price_cents"] == int(round(7900 * 1.5 * 0.9))
    r = client.patch("/admin/products/feather-flag", json={"active": False}, headers=admin)
    assert r.status_code == 200
    assert client.get("/products/feather-flag").status_code == 404
