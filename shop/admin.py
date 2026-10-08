from django.conf import settings

from django.contrib import admin

from shop.models import Order, OrderItem, Package, Product




# Register your models here.
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)



@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
  list_display=(
    "name", "price", "interval", "max_products"
  )


