# Shop API

A Django REST Framework backend for an e-commerce flow: product listing, guest-friendly cart, JWT auth, and Stripe Checkout payment with webhook-confirmed stock management.

## Live demo

API base URL: `https://your-app.onrender.com/api/`
Interactive docs (Swagger): `https://your-app.onrender.com/docs/`

> Free-tier hosting — first request after inactivity may take ~30s to wake up.

## Features

- JWT-based auth (register/login/refresh) — no session/cookie auth
- Public product browsing, owner-gated create/update/delete
- Anonymous-friendly cart via `X-Cart-Id` header, merges into the user's cart on login
- Stripe Checkout integration for card payments
- Webhook-confirmed order finalization — stock only decrements once payment is verified, not on checkout attempt
- Auto-generated OpenAPI schema + Swagger UI via drf-spectacular

## Tech stack

- Django 6 / Django REST Framework
- PostgreSQL
- Stripe (Checkout Sessions + Webhooks)
- JWT auth via `djangorestframework-simplejwt`
- `drf-spectacular` for OpenAPI docs

## API overview

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/auth/register/` | POST | — | Create account |
| `/api/auth/login/` | POST | — | Get JWT access/refresh tokens |
| `/api/auth/refresh/` | POST | — | Refresh access token |
| `/api/products/` | GET | — | List products |
| `/api/products/` | POST | JWT | Create product (becomes owner) |
| `/api/products/<id>/` | GET | — | Product detail |
| `/api/products/<id>/` | PUT/PATCH/DELETE | JWT (owner only) | Edit/delete own product |
| `/api/cart/` | GET | optional | View cart (`X-Cart-Id` header for guests) |
| `/api/cart/add/` | POST | optional | Add item to cart |
| `/api/cart/remove/<product_id>/` | DELETE | optional | Remove item |
| `/api/checkout/` | POST | JWT | Create order + Stripe Checkout session |
| `/api/stripe/webhook/` | POST | Stripe only | Payment confirmation, decrements stock |
| `/api/orders/` | GET | JWT | List own orders |
| `/api/orders/<id>/` | GET | JWT | Order detail |

Full interactive docs with request/response schemas: `/docs/`

## Local setup

```bash
git clone <repo-url>
cd shop
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

cp .env.example .env           # fill in real values
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Stripe webhook locally

```bash
stripe listen --events checkout.session.completed --forward-to localhost:8000/api/stripe/webhook/
```
Copy the printed `whsec_...` into `.env` as `STRIPE_WEBHOOK_SECRET`.

## Environment variables

See `.env.example` for the full list. Required: `SECRET_KEY`, `DB_*`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `FRONTEND_URL`.

## Testing the full flow

1. `POST /api/auth/register/` then `/login/` → copy `access` token
2. Authorize in Swagger with `Bearer <token>`
3. `POST /api/cart/add/` with a product id
4. `POST /api/checkout/` with delivery details → returns `checkout_url`
5. Open `checkout_url`, pay with Stripe test card `4242 4242 4242 4242`
6. Webhook confirms payment → order status flips to `paid`, product stock decrements

## Notes

- Backend-only — no templates/HTML. Built to be consumed by a separate frontend (web/mobile).
- Stock is reserved at checkout creation time implicitly (cart is cleared), but only **confirmed** (decremented) once Stripe's webhook verifies payment — prevents overselling from abandoned checkouts while avoiding double-decrement races via `select_for_update`.