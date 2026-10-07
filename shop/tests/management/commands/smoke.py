from django.core.management.base import BaseCommand, CommandError
from rest_framework.test import APIClient
from shop.models import Product


class Command(BaseCommand):
    help = "End-to-end: multi-item cart -> checkout -> prints Stripe URL"

    def _ok(self, name, r, expect):
        if r.status_code != expect:
            raise CommandError(f"{name}: {r.status_code} {getattr(r, 'data', r.content)}")
        return r

    def handle(self, *args, **opts):
        c = APIClient(SERVER_NAME="localhost")
        products = list(Product.objects.order_by("id")[:3])
        if len(products) < 2:
            raise CommandError("run seed_test first")

        r = self._ok("add 1", c.post(
            "/api/cart/add/", {"product_id": products[0].id, "qty": 2}, format="json"), 201)
        h = {"HTTP_X_CART_ID": r.data["id"]}
        for p in products[1:]:
            self._ok(f"add {p.id}", c.post(
                "/api/cart/add/", {"product_id": p.id, "qty": 1}, format="json", **h), 201)

        r = self._ok("login", c.post(
            "/api/auth/login",
            {"username": "tester", "password": "pass12345"},
            format="json"), 200)
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

        r = self._ok("checkout", c.post(
            "/api/checkout/",
            {
                "full_name": "Test",
                "phone": "0123456789",
                "address_line": "1 Test St",
                "city": "Dhaka",
                "postal_code": "1200",
            },
            format="json", **h), 201)
        self.stdout.write(f"order={r.data['order_id']}")
        self.stdout.write(f"pay: {r.data['checkout_url']}")