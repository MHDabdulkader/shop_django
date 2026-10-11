from typing import Any

from django.conf import settings

from django.contrib import admin
from django.http import HttpRequest

from shop.models import Order, OrderItem, Package, Product, Subscription
from shop.services import sync_package_to_stripe




# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
  list_display=("name", "price", "stock", "created_at", "updated_at")
  search_fields=("name", "price", "stock")
  list_filter=("price", "stock")
  
class OrderItemInline(admin.TabularInline):
  model = OrderItem
  extra=0
  readonly_fields=("product", "qty", "price")
  can_delete=False
  
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
  list_display=("id", "user", "status", "total", "created_at")
  list_filter = ("status", "created_at")
  search_fields = ("id", "user__email", "user_username")
  date_hierarchy= "created_at"
  ordering=("-id", "-created_at")
  list_per_page=25
  inlines=[OrderItemInline]
  
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
  list_display = ("id", "order", "product", "qty", "price")
  list_select_related=("order", "product")  
# admin.site.register(Product)
# admin.site.register(Order)
# admin.site.register(OrderItem)



@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
  list_display=(
    "name", "price", "interval", "max_products",
    "max_stock_per_product", "can_feature_products", "is_active", "stripe_price_id"
  )
  fields = (
    "name", "price", "interval", "is_active", "max_products", "max_stock_per_product", "can_feature_products"
  )
  
  def save_model(self, request: HttpRequest, obj: Any, form: Any, change: Any) -> None:
    super().save_model(request, obj, form, change)
    sync_package_to_stripe(obj, set(form.changed_data))
    
@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
  list_display = (
    "user", "package", "status", "current_period_end"
    )

  readonly_fields=(
    "user", "package", "status", "stripe_customer_id", "stripe_subscription_id",
    "current_period_end", "cancel_at_period_end"
  )



