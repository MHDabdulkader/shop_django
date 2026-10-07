from unittest.mock import MagicMock, patch
from rest_framework.test import APITestCase

from shop.models import Order
from .factories import make_product, make_user

DELIVERY = {
    "full_name": "ProductOwnerName",
    "phone": "0123456789",
    "address_line": "Dhaka, Bangladesh",
    "city": "Dhaka",
    "postal_code": "1234",
}


class CheckoutTests(APITestCase):
    @patch("shop.payments.stripe.checkout.Session.create")
    def test_checkout_creates_order_and_clears_cart(self, create):
        create.return_value = MagicMock(id="cs_1", url="https://stripe.test/pay")
        u = make_user()
        a = make_product(u, "A", price=40, stock=20)
        b = make_product(u, "B", price=50, stock=20)

        r = self.client.post(
            "/api/cart/add/", {"product_id": a.id, "qty": 10}, format="json"
        )
        self.assertEqual(r.status_code, 201)
        h = {"HTTP_X_CART_ID": r.data["id"]}
        r = self.client.post(
            "/api/cart/add/", {"product_id": b.id, "qty": 15}, format="json", **h
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(len(r.data["items"]), 2)

        self.client.force_authenticate(u)
        r = self.client.post("/api/checkout/", DELIVERY, format="json", **h)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["checkout_url"], "https://stripe.test/pay")
        self.assertEqual(len(create.call_args.kwargs["line_items"]), 2)

        order = Order.objects.get(pk=r.data["order_id"])
        self.assertEqual(order.total, 40 * 10 + 50 * 15)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.status, "pending")
        # cart emptied (and stock NOT touched until the webhook)
        a.refresh_from_db()
        self.assertEqual(a.stock, 20)
