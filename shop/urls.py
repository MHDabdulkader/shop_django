from django.urls import path
from . import views as V
from .payments import CheckoutView, stripe_webhook
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("auth/register", V.RegisterView.as_view(), name="Register"),
    path("auth/login", V.LoginView.as_view(), name="Login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="Refresh Token"),
    path(
        "products/",
        V.ProductViewSet.as_view({"get": "list", "post": "create"}),
        name="Product",
    ),
    path(
        "products/<int:pk>/",
        V.ProductViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),
    
    
    path("cart/", V.CartDetailsView.as_view()),
    path("cart/add/", V.CartAddView.as_view()),
    path("cart/remove/<int:product_id>", V.CartRemoveView.as_view()),
    
    path("checkout/", CheckoutView.as_view()),
    path("stripe/webhook", stripe_webhook),
    
    
    path("orders/", V.OrderListView.as_view()),
    path("orders/<int:pk>", V.OrderDetailsView.as_view()) 
]
