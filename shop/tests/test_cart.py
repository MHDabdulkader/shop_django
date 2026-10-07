from rest_framework.test import APITestCase
from .factories import make_product, make_user


class CartTest(APITestCase):
    def test_multi_item_cart_same_id(self):
        u = make_user()
        a = make_product(u, "A", price=10)
        b = make_product(u, "B", price=20)

        r = self.client.post("/api/cart/add/", {"product_id": a.id, "qty": 2}, format="json")
        self.assertEqual(r.status_code, 201)
        h = {"HTTP_X_CART_ID": r.data["id"]}

        r = self.client.post("/api/cart/add/", {"product_id": b.id, "qty": 1}, format="json", **h)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(len(r.data["items"]), 2)
        self.assertEqual(float(r.data["total"]), 40.0)