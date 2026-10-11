from datetime import datetime, timezone


from django.conf import settings
import stripe

from shop.models import Subscription


stripe.api_key = settings.STRIPE_SECRET_KEY

def sync_package_to_stripe(pkg, changed):
  """Changed: set of field names that changed (empty/None fields on create)."""
  # * product
  if not pkg.stripe_product_id:
    pkg.stripe_product_id = stripe.Product.create(name=pkg.name)["id"]
  elif "name" in changed:
    stripe.Product.modify(pkg.stripe_product_id, name=pkg.name)
    
  if not pkg.stripe_price_id or {"price", "interval"} & changed :
    if pkg.stripe_price_id:
      stripe.Price.modify(pkg.stripe_price_id, active=False) # * change status but price immutated
    
    # * Price  
    pkg.stripe_price_id = stripe.Price.create(
      product=pkg.stripe_product_id,
      unit_amount=int(pkg.price * 100),
      currency="usd",
      recurring={'interval': pkg.interval}
    )["id"]
  
  if "is_active" in changed:
    stripe.Product.modify(pkg.stripe_product_id, active=pkg.is_active)
    
  pkg.save(update_fields=["stripe_product_id", "stripe_price_id"])
  
def create_subscription_checkout(user, package, success_url, cancel_url):
  return stripe.checkout.Session.create( 
    mode="subscription",
    line_items=[{"price": package.stripe_price_id, "quantity": 1}],
    success_url=success_url,
    cancel_url=cancel_url,
    client_reference_id=str(user.pk)
    metadata={"user_id": str(user.pk), "package_id":str(package.pk)},
    subscription_data={"metadata=": {"user_id": str(user.pk), "package_id": str(package.pk)}},
  )
  
def handle_checkout_completed(session):
  if session["mode"] != "subscription":
    return 
  
  sub = stripe.Subscription.retrieve(session["subscription"])
  Subscription.objects.update_or_create(
    user_id = session["metadata"]["user_id"],
    defaults=dict(
      package_id=session["metadata"]["package_id"],
      stripe_customer_id = session["customer"],
      stripe_subscription_id = sub["id"],
      status = sub["status"],
      current_period_end=datetime.fromtimestamp(sub["current_period_end"], tz=timezone.utc),
      cancel_at_period_end = sub["cancel_at_period_end"]
    )
  )
    
    