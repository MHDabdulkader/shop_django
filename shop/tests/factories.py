# shared helpers
from django.contrib.auth import get_user_model

from shop.models import Order, OrderItem, Product
# from shop.models import 


User = get_user_model()

def make_user(name="t"):
  return User.objects.create_user(name, password="x")

def make_product(owner, name="ProductOwner", price = 10, stock = 20):
  return Product.objects.create(owner=owner, name=name, price=price, stock=stock)

def make_order(user, lines, session="cs_test"):
  """lines = [(product, qty), ...]"""
  o = Order.objects.create(
    user=user, 
    total=sum(p.price* q for p, q in lines),
    full_name="ProductOwnerName",
    phone="0123456789",
    address_line="Dhaka, Bangladesh",
    city="Dhaka",
    postal_code="1234",
    stripe_session_id=session
  )
  
  for p, q in lines:
    OrderItem.objects.create(order=o, product=p, name=p.name, price=p.price, qty=q)
  
  return o 
