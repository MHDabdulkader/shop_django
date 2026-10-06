from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Product, Order, OrderItem, Cart, CartItem

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
  password = serializers.CharField(write_only=True, validators=[validate_password])
  
  class Meta:
    model = User
    fields = ["id", "username", "email", "password"]
    
  def create(self, validated_data):
    return User.objects.create_user(**validated_data)

class ProductSerializer(serializers.ModelSerializer):
  class Meta:
    model = Product
    fields = ["id", "owner", "name", "description", "price", "stock", "image", "created_at", "updated_at"]
    read_only_fields=["owner"]
 
 
class CartAddSerializer(serializers.Serializer):
  product_id = serializers.IntegerField()
  qty = serializers.IntegerField(default=1, min_value=1)
   
    
class CartItemsSerializer(serializers.ModelSerializer):
  product = ProductSerializer(read_only=True)
  product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source="product", write_only=True)
  subtotal = serializers.SerializerMethodField()
  
  class Meta:
    model = CartItem
    fields = ["id", "product", "product_id", "qty", "subtotal"]
    
  def get_subtotal(self, obj):
    return obj.product.price * obj.qty
  
class CartSerializer(serializers.ModelSerializer):
  items  = CartItemsSerializer(many=True, read_only=True)
  total = serializers.SerializerMethodField()
  
  class Meta:
    model = Cart
    fields = ["id", "items", "total"]
    
  def get_total(self, obj):
    return sum(i.product.price*i.qty  for i in obj.items.all())
  
class DeliverySerializer(serializers.Serializer):
  full_name = serializers.CharField(max_length=255)
  phone = serializers.CharField(max_length = 20)
  address_line = serializers.CharField(max_length=255)
  city = serializers.CharField(max_length=255)
  postal_code = serializers.CharField(max_length=20)
  

class OrderItemSerializer(serializers.ModelSerializer):
  class Meta:
    model = OrderItem
    fields = ["id", "name", "price", "qty"]
    
class OrderSerializer(serializers.ModelSerializer):
  items = OrderItemSerializer(many=True, read_only=True)
  
  class Meta:
    model = Order
    fields = ["id", "status", "total", "created_at", "updated_at", "full_name", "phone", "address_line", "city", "postal_code", "items"]
        