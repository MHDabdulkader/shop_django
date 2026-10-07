# stock/refund logic

from unittest.mock import MagicMock, patch
from django.test import TestCase
from shop.models import Product
from shop.payments import _finalize_order
from .factories import make_order, make_product, make_user



class FinalizeTests(TestCase):
    def setUp(self):
        self.u = make_user()
        self.a = make_product(self.u, "A", stock=5)
        self.b = make_product(self.u, "B", stock=5)
        self.order = make_order(self.u, [(self.a, 2), (self.b, 1)])

    def _reload(self):
        for o in (self.order, self.a, self.b):
            o.refresh_from_db()

    def test_paid_decrements_each_product(self):
        a0, b0 = self.a.stock, self.b.stock
        _finalize_order(self.order.id)
        self._reload()
        self.assertEqual(self.order.status, "paid")
        self.assertEqual(self.a.stock, a0 - 2)
        self.assertEqual(self.b.stock, b0 - 1)

    def test_idempotent(self):
        _finalize_order(self.order.id)
        self._reload()
        after_first = (self.a.stock, self.b.stock)
        _finalize_order(self.order.id)
        self._reload()
        self.assertEqual((self.a.stock, self.b.stock), after_first)

    @patch("shop.payments.stripe.Refund.create")
    @patch("shop.payments.stripe.checkout.Session.retrieve")
    def test_oversold_no_partial_decrement_and_refund(self, retrieve, refund):
        retrieve.return_value = MagicMock(payment_intent="pi_1")
        a0 = self.a.stock
        Product.objects.filter(pk=self.b.pk).update(stock=0)
        _finalize_order(self.order.id)
        self._reload()
        self.assertEqual(self.order.status, "cancelled")
        self.assertEqual(self.a.stock, a0)
        refund.assert_called_once()