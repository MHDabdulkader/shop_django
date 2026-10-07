from unittest.mock import MagicMock, patch
from django.test import TestCase
from .factories import make_order, make_user, make_product


class WebhookTests(TestCase):
  @patch("shop.payments._finalize_order")
  @patch("shop.payments.stripe.Webhook.construct_event")
  def test_paid_event_finalizes(self, construct, finalize):
    obj = MagicMock()
    obj.to_dict.return_value = {"metadata": {"order_id": "7"}, "payment_status": "paid"}
    construct.return_value ={"type": "checkout.session.completed", "data": {"object": obj}}
    
    r = self.client.post("/api/stripe/webhook",data=b"{}",
                         content_type="application/json",
                         HTTP_STRIPE_SIGNATURE="x"
                         )
    self.assertEqual(r.status_code, 200)
    
    finalize.assert_called_once_with("7")
    
  
  def test_bad_signature_400(self):
    r = self.client.post("/api/stripe/webhook", data=b"{}",
                         content_type="application/json",
                         HTTP_STRIPE_SIGNATURE="bad"
                         )
    self.assertEqual(r.status_code, 400)
    
  