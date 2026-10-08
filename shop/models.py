from uuid import uuid4
import uuid

from django.db import models
from django.conf import settings
# Create your models here.

class Product(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"] # ! check other sort need ordering?

class Cart(models.Model):
    """Anonymous-friendly cart. Client generate a UUID and stores it locally
    (localstorage/Asyncstorage), passes it as X-Cart-Id header on every request.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")

class Order(models.Model):
    STATUS = [("pending", "Pending"), ("paid", "Paid"), ("cancelled", "Cancelled")]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=10, choices=STATUS,  default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    stripe_session_id = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    qty = models.PositiveIntegerField()



# * Package and subscription:
class Package(models.Model):
    INTERVALS = [("month", "Monthly"), ("year", "Yearly")]
    
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    interval = models.CharField(max_length=8, choices=INTERVALS, default="month")
    is_active = models.BooleanField(default=True) # * Change via admin
    
    # * Features (practice limits)
    max_products = models.PositiveIntegerField(default=5)
    max_stock_per_product = models.PositiveIntegerField(default=50)
    can_feature_products = models.BooleanField(default=False)
    
    # * filled automatically by admin sync
    stripe_product_id = models.CharField(max_length=100, blank=True, editable=False)
    stripe_price_id = models.CharField(max_length=100, blank=True, editable=False)
    
    def __str__(self) -> str:
        return f"{self.name} ({self.price}/{self.interval})"
    
class Subscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription")
    package = models.ForeignKey(Package, on_delete=models.PROTECT)
    stripe_customer_id = models.CharField(max_length=100)
    stripe_subscription_id = models.CharField(max_length=100)
    status = models.CharField(max_length=100) # * active, trialing, past_due, cancelled
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def is_active(self):
        return self.status in ("active", "trialing")
    
    
def active_package(user):
    sub = getattr(user, "subscription", None)
    return sub.package if sub and sub.is_active else None


    