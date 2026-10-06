from django.contrib import admin

from shop.models import Order, OrderItem, Product

# Register your models here.
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)