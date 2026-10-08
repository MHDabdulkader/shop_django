from django.conf import settings
import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY

def sync_package_to_stripe(pkg, changed):
  """Changed: set of field names that changed (empty/None fields on create)."""
  # * product
  if not pkg.stripe_product_id:
    pkg.stripe_product_id = stripe.Product.create(name=pkg.name)["id"]
  elif "name" in changed:
    stripe.Product.modify(pkg.stripe_product_id, name=pkg.name)
    
  if not pkg.stipe_price_id or {"price", "interval"} & changed :
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
    
    