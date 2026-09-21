# Print Ordering Backend

FastAPI + SQLAlchemy backend for a custom print shop (table runners, banners, displays, posters).
Customers configure a product, get an instant price, upload artwork, pay through Stripe Checkout,
and the shop reviews the artwork afterwards: approve it, reject it with a reason so the customer
re-uploads, or send a digital proof the customer approves before production.

## Flow

```
Customer                                   Shop (admin)
--------                                   ------------
configure product + quantity  -> quote
add to cart, upload artwork (preflight: DPI, aspect ratio, page size)
checkout (address, shipping) -> Stripe Checkout
pay  -> webhook -> order: paid -> in_review
                                           review queue
                                           approve item        -> approved -> in_production -> shipped -> completed
                                           reject item (reason)-> awaiting_customer
re-upload fixed artwork      -> in_review
                                           send proof           -> awaiting_customer
approve proof / request changes
                                           cancel + full refund -> refunded
```

Order status: `cart, pending_payment, paid, in_review, awaiting_customer, approved, in_production, shipped, completed, cancelled, refunded`.
Item artwork status: `awaiting_artwork, submitted, rejected, proof_sent, changes_requested, approved`.
Every transition is written to `order_events` with the actor, so the order page shows a full history.

## Run locally

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                         # defaults: sqlite, local storage, fake payments, console email
.venv/bin/python -m scripts.seed --admin-email admin@example.com --admin-password change-me-now
.venv/bin/uvicorn app.main:app --reload
```

Open http://localhost:8000/docs. With `PAYMENT_PROVIDER=fake`, `POST /payments/{payment_id}/simulate`
stands in for the Stripe webhook so the whole flow can be exercised without a Stripe account.

Tests: `.venv/bin/python -m pytest`

## Production

Set in the environment: `ENVIRONMENT=production`, a long `SECRET_KEY`, `DATABASE_URL` (Postgres),
`STORAGE_BACKEND=s3` with `S3_BUCKET` (works with S3, R2 and MinIO via `S3_ENDPOINT_URL`),
`PAYMENT_PROVIDER=stripe` with `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`, `EMAIL_BACKEND=smtp`
with the SMTP settings, and `FRONTEND_URL` (used for CORS, checkout redirects and email links).
Point the Stripe webhook at `/webhooks/stripe` for the `checkout.session.completed` event.
Run `alembic upgrade head` on deploy; tables are only auto-created outside production.

## API

Auth: `POST /auth/register`, `POST /auth/login` (form: username, password), `GET /auth/me`

Catalog (public): `GET /products`, `GET /products/{slug}`, `POST /products/{slug}/quote`

Cart: `GET /cart`, `POST /cart/items`, `PATCH /cart/items/{id}`, `DELETE /cart/items/{id}`,
`POST /cart/items/{id}/artwork` (multipart), `POST /cart/checkout` -> `checkout_url`

Orders: `GET /orders`, `GET /orders/{id}`, `POST /orders/{id}/reopen`,
`POST /orders/{id}/items/{item}/artwork` (re-upload after rejection),
`POST /orders/{id}/items/{item}/proof/approve`, `POST /orders/{id}/items/{item}/proof/request-changes`,
`GET /orders/{id}/artworks/{artwork}/download?preview=1`

Payments: `POST /webhooks/stripe`, `POST /payments/{id}/simulate` (fake provider only)

Admin: `GET /admin/orders`, `GET /admin/orders/review-queue`, `GET /admin/orders/{id}`,
`POST /admin/orders/{id}/items/{item}/approve | reject | proof`,
`POST /admin/orders/{id}/production | ship | complete | reopen-review | cancel`,
`POST /admin/products`, `PATCH /admin/products/{slug}`

## Catalog model

A product is data, not code. `pricing_config` sets the base price (`unit` or per square foot `area`),
the size presets or custom size range, accepted file types and minimum DPI. Option groups
(material, print sides, finishing, turnaround) carry choices priced as a multiplier, a flat amount,
per square foot or per unit. Quantity tiers apply a percentage discount. `app/services/seed.py`
holds the starter catalog and is the reference for adding products.

## Layout

```
app/core        settings, password hashing, JWT
app/models      users, catalog, orders, items, artworks, events, payments
app/services    pricing, artwork inspection, storage, payments, notifications, order state machine
app/api/routes  auth, products, cart, orders, payments, admin
alembic         migrations
scripts/seed.py catalog + admin bootstrap
tests           end to end flow tests against sqlite and the fake payment provider
```
