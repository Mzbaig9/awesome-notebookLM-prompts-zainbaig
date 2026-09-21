import io

from tests.conftest import ADDRESS, pdf_bytes, png_bytes


def add_runner(client, headers, quantity=1):
    r = client.post("/cart/items", json={"product_slug": "table-runner", "quantity": quantity, "size_preset": "2x5.7"}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def upload(client, headers, item_id, data, name):
    return client.post(f"/cart/items/{item_id}/artwork", files={"file": (name, io.BytesIO(data), "application/octet-stream")}, headers=headers)


def checkout_and_pay(client, headers):
    r = client.post("/cart/checkout", json={"shipping_method": "standard", "shipping_address": ADDRESS}, headers=headers)
    assert r.status_code == 200, r.text
    co = r.json()
    assert co["checkout_url"].startswith("http://front.test/fake-checkout/")
    r = client.post(f"/payments/{co['payment_id']}/simulate", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_cart_pricing_and_edit(client, customer):
    cart = add_runner(client, customer, quantity=2)
    item = cart["items"][0]
    assert item["unit_price_cents"] == int(round(4900 * 0.95))
    assert cart["subtotal_cents"] == item["line_total_cents"]
    r = client.patch(f"/cart/items/{item['id']}", json={"quantity": 1, "options": {"print_sides": "double"}}, headers=customer)
    assert r.status_code == 200, r.text
    assert r.json()["items"][0]["unit_price_cents"] == int(round(4900 * 1.6))
    r = client.delete(f"/cart/items/{item['id']}", headers=customer)
    assert r.json()["items"] == []


def test_checkout_requires_artwork_unless_design_later(client, customer):
    cart = add_runner(client, customer)
    r = client.post("/cart/checkout", json={"shipping_method": "standard", "shipping_address": ADDRESS}, headers=customer)
    assert r.status_code == 400
    assert "needs artwork" in r.json()["detail"]
    item_id = cart["items"][0]["id"]
    r = client.patch(f"/cart/items/{item_id}", json={"design_service": "design_later"}, headers=customer)
    assert r.status_code == 200
    order = checkout_and_pay(client, customer)
    assert order["status"] == "in_review"
    assert order["items"][0]["artwork_status"] == "awaiting_artwork"
    assert order["shipping_cents"] == 1500
    assert order["total_cents"] == 4900 + 1500


def test_artwork_validation_and_preflight(client, customer):
    cart = add_runner(client, customer)
    item_id = cart["items"][0]["id"]
    r = upload(client, customer, item_id, b"hello", "art.docx")
    assert r.status_code == 422
    r = upload(client, customer, item_id, b"not a png", "art.png")
    assert r.status_code == 422
    # 240x680 px on a 24x68 in runner is 10 dpi, below the 100 dpi minimum
    r = upload(client, customer, item_id, png_bytes(240, 680), "art.png")
    assert r.status_code == 201, r.text
    art = r.json()
    assert art["version"] == 1 and art["has_preview"] is True
    assert art["file_metadata"]["effective_dpi"] == 10
    assert any("Low resolution" in w for w in art["warnings"])
    r = upload(client, customer, item_id, pdf_bytes(24, 68), "art.pdf")
    assert r.status_code == 201
    assert r.json()["version"] == 2 and r.json()["warnings"] == []
    order_id = cart["id"]
    r = client.get(f"/orders/{order_id}/artworks/{art['id']}/download?preview=1", headers=customer)
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"


def test_full_flow_approve_production_ship(client, customer, admin):
    cart = add_runner(client, customer)
    item_id = cart["items"][0]["id"]
    assert upload(client, customer, item_id, pdf_bytes(), "art.pdf").status_code == 201
    order = checkout_and_pay(client, customer)
    oid = order["id"]
    assert order["status"] == "in_review"
    assert order["payments"][0]["status"] == "paid"
    assert [e["event_type"] for e in order["events"]][-3:] == ["checkout_started", "payment_confirmed", "review_started"]

    # cart is now locked, and the customer got a fresh empty cart
    assert client.get("/cart", headers=customer).json()["items"] == []
    assert oid in [o["id"] for o in client.get("/admin/orders/review-queue", headers=admin).json()]

    # customer cannot use admin endpoints
    assert client.post(f"/admin/orders/{oid}/items/{item_id}/approve", json={}, headers=customer).status_code == 403

    r = client.post(f"/admin/orders/{oid}/items/{item_id}/approve", json={"note": "Looks good"}, headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "approved"
    assert r.json()["items"][0]["artwork_status"] == "approved"

    # cannot ship before production
    assert client.post(f"/admin/orders/{oid}/ship", json={}, headers=admin).status_code == 409
    assert client.post(f"/admin/orders/{oid}/production", json={}, headers=admin).json()["status"] == "in_production"
    r = client.post(f"/admin/orders/{oid}/ship", json={"tracking_number": "1Z999"}, headers=admin)
    assert r.json()["status"] == "shipped" and r.json()["tracking_number"] == "1Z999"
    assert client.post(f"/admin/orders/{oid}/complete", headers=admin).json()["status"] == "completed"

    mine = client.get("/orders", headers=customer).json()
    assert [o["id"] for o in mine] == [oid]


def test_reject_reupload_proof_cycle(client, customer, admin):
    cart = add_runner(client, customer)
    item_id = cart["items"][0]["id"]
    assert upload(client, customer, item_id, pdf_bytes(), "art.pdf").status_code == 201
    order = checkout_and_pay(client, customer)
    oid = order["id"]

    r = client.post(f"/admin/orders/{oid}/items/{item_id}/reject", json={"reason": "Text is inside the bleed"}, headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "awaiting_customer"
    assert r.json()["items"][0]["artwork_status"] == "rejected"
    assert r.json()["items"][0]["review_note"] == "Text is inside the bleed"

    # customer re-uploads through the order endpoint (cart endpoint no longer applies)
    r = client.post(f"/orders/{oid}/items/{item_id}/artwork", files={"file": ("fixed.pdf", io.BytesIO(pdf_bytes()), "application/pdf")}, headers=customer)
    assert r.status_code == 201, r.text
    assert r.json()["version"] == 2
    order = client.get(f"/orders/{oid}", headers=customer).json()
    assert order["status"] == "in_review"
    assert order["items"][0]["artwork_status"] == "submitted"

    # admin sends a proof, customer asks for changes, admin sends another, customer approves
    r = client.post(f"/admin/orders/{oid}/items/{item_id}/proof", files={"file": ("proof.pdf", io.BytesIO(pdf_bytes()), "application/pdf")},
                    data={"note": "Please confirm colours"}, headers=admin)
    assert r.status_code == 201, r.text
    assert r.json()["kind"] == "proof"
    order = client.get(f"/orders/{oid}", headers=customer).json()
    assert order["status"] == "awaiting_customer" and order["items"][0]["artwork_status"] == "proof_sent"

    r = client.post(f"/orders/{oid}/items/{item_id}/proof/request-changes", json={"note": "Logo is too small"}, headers=customer)
    assert r.status_code == 200 and r.json()["artwork_status"] == "changes_requested"
    assert client.get(f"/orders/{oid}", headers=customer).json()["status"] == "in_review"

    r = client.post(f"/admin/orders/{oid}/items/{item_id}/proof", files={"file": ("proof2.pdf", io.BytesIO(pdf_bytes()), "application/pdf")}, headers=admin)
    assert r.status_code == 201 and r.json()["version"] == 2
    r = client.post(f"/orders/{oid}/items/{item_id}/proof/approve", headers=customer)
    assert r.status_code == 200 and r.json()["artwork_status"] == "approved"
    assert client.get(f"/orders/{oid}", headers=customer).json()["status"] == "approved"


def test_refund_on_cancel_after_payment(client, customer, admin):
    cart = add_runner(client, customer)
    item_id = cart["items"][0]["id"]
    assert upload(client, customer, item_id, pdf_bytes(), "art.pdf").status_code == 201
    order = checkout_and_pay(client, customer)
    oid = order["id"]
    r = client.post(f"/admin/orders/{oid}/cancel", json={"note": "Customer asked to cancel"}, headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "refunded"
    pay = r.json()["payments"][0]
    assert pay["status"] == "refunded" and pay["refund_id"].startswith("fake_re_")
    # nothing further is allowed
    assert client.post(f"/admin/orders/{oid}/production", json={}, headers=admin).status_code == 409


def test_webhook_confirms_payment_idempotently(client, customer):
    cart = add_runner(client, customer)
    item_id = cart["items"][0]["id"]
    assert upload(client, customer, item_id, pdf_bytes(), "art.pdf").status_code == 201
    r = client.post("/cart/checkout", json={"shipping_method": "express", "shipping_address": ADDRESS}, headers=customer)
    assert r.status_code == 200, r.text
    session_id = r.json()["checkout_url"].rsplit("/", 1)[-1]
    oid = r.json()["order_id"]
    assert client.get(f"/orders/{oid}", headers=customer).json()["status"] == "pending_payment"
    payload = {"type": "checkout.session.completed", "session_id": session_id, "payment_intent_id": "pi_1"}
    for _ in range(2):
        r = client.post("/webhooks/stripe", json=payload)
        assert r.status_code == 200 and r.json()["handled"] is True
    order = client.get(f"/orders/{oid}", headers=customer).json()
    assert order["status"] == "in_review"
    assert order["shipping_cents"] == 3500
    assert sum(1 for e in order["events"] if e["event_type"] == "payment_confirmed") == 1
    r = client.post("/webhooks/stripe", json={"type": "checkout.session.completed", "session_id": "cs_unknown"})
    assert r.json()["handled"] is False


def test_reopen_pending_checkout(client, customer):
    cart = add_runner(client, customer)
    item_id = cart["items"][0]["id"]
    assert upload(client, customer, item_id, pdf_bytes(), "art.pdf").status_code == 201
    r = client.post("/cart/checkout", json={"shipping_method": "standard", "shipping_address": ADDRESS}, headers=customer)
    oid = r.json()["order_id"]
    # cart is locked while payment is pending
    assert client.post("/cart/items", json={"product_slug": "poster", "quantity": 1, "size_preset": "18x24"}, headers=customer).status_code == 409
    r = client.post(f"/orders/{oid}/reopen", headers=customer)
    assert r.status_code == 200 and r.json()["status"] == "cart"
    assert client.get("/cart", headers=customer).json()["id"] == oid


def test_other_customer_cannot_see_order(client, customer, admin):
    cart = add_runner(client, customer)
    oid = cart["id"]
    r = client.post("/auth/register", json={"email": "other@test.com", "password": "otherpass123"})
    assert r.status_code == 201
    r = client.post("/auth/login", data={"username": "other@test.com", "password": "otherpass123"})
    other = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get(f"/orders/{oid}", headers=other).status_code == 404
    assert client.get(f"/admin/orders/{oid}", headers=admin).status_code == 200
