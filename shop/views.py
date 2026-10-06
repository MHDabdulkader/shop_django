

from shop.models import CartItem, Product
from shop.permission import IsOwnerOrReadOnly
from shop.utils import CART_ID_PARAM, get_cart

from shop.serializers import CartItemsSerializer, CartSerializer, OrderSerializer, ProductSerializer, RegisterSerializer, CartAddSerializer
from rest_framework.permissions import  AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework.response import Response
from rest_framework import generics, viewsets, status

from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema



# from .stripe import _get_cart



# * __ Auth Register _________________________________________
class RegisterView(generics.CreateAPIView):
  serializer_class= RegisterSerializer
  permission_classes=[AllowAny]
  

class LoginView(TokenObtainPairView):
  permission_classes=[AllowAny]
  


# * __ Product ________________________________________________
class ProductViewSet(viewsets.ModelViewSet):
  queryset = Product.objects.all()
  serializer_class = ProductSerializer
  permission_classes = [IsOwnerOrReadOnly]
  
  def get_permissions(self):
    if self.action == "create":
      return [IsAuthenticated()]
    return super().get_permissions()
  
  def perform_create(self, serializer):
    serializer.save(owner=self.request.user)
    
    
# * __ Cart _____________________________________________________
class CartDetailsView(APIView):
  permission_classes = [AllowAny]
  @extend_schema(parameters=[CART_ID_PARAM] ,responses=CartSerializer)
  def get(self, request):
    return Response(CartSerializer(get_cart(request)).data)
  

class CartAddView(APIView):
  permission_classes = [AllowAny]
  
  @extend_schema(request=CartAddSerializer, responses=CartSerializer)
  def post(self, request):
    serializer = CartAddSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    cart = get_cart(request)
    product = Product.objects.get(pk = serializer.validated_data["product_id"]) # type: ignore[assignment]
    qty = serializer.validated_data["qty"] # type: ignore[assignment]
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"qty":qty})
    
    if not created:
      item.qty += qty # type: ignore[assignment]
      item.save(update_fields=["qty"])
      
    return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)
  
class CartRemoveView(APIView):
  permission_classes = [AllowAny]
  
  @extend_schema(parameters=[CART_ID_PARAM],responses=CartSerializer)
  def delete(self, request, product_id):
    cart = get_cart(request)
    CartItem.objects.filter(cart=cart, product_id = product_id).delete()
    
    return Response(CartSerializer(cart).data)
  


# * __ Orders _________________________________________
class OrderListView(generics.ListAPIView):
  serializer_class = OrderSerializer
  permission_classes=[IsAuthenticated]
  
  def get_queryset(self):
    return self.request.user.orders.all()
  
class OrderDetailsView(generics.RetrieveAPIView):
  serializer_class = OrderSerializer
  permission_classes = [IsAuthenticated]
  
  def get_queryset(self):
    return self.request.user.orders.all()
  