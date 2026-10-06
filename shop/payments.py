from django.conf import settings

from django.db import transaction
from django.http import HttpResponse
import stripe


from shop.models import Cart, Order, OrderItem, Product
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)

from drf_spectacular.utils import extend_schema

from django.views.decorators.csrf import csrf_exempt

from shop.serializers import DeliverySerializer
from shop.utils import CART_ID_PARAM, get_cart

import logging
logger = logging.getLogger("shop")

# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY


def _get_cart(request):
    cart_id = request.headers.get("X-Cart-Id") or request.query_params.get("cart_id")
    cart, _ = (
        Cart.objects.get_or_create(id=cart_id)
        if cart_id
        else (Cart.objects.create(), False)
    )
    return cart


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]


    @extend_schema(parameters=[CART_ID_PARAM], request=DeliverySerializer)
    def post(self, request):
        cart = get_cart(request)
        items = list(cart.items.select_related("product"))

        if not items:
            return Response({"detail": "Cart is empty"}, status=400)

        delivery = DeliverySerializer(data=request.data)
        delivery.is_valid(raise_exception=True)

        order = Order.objects.create(
            user=request.user,
            total=sum(i.product.price * i.qty for i in items),
            **delivery.validated_data,
        )
        for i in items:
            OrderItem.objects.create(
                order=order,
                product=i.product,
                name=i.product.name,
                price=i.product.price,
                qty=i.qty,
            )

        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": item.name},
                        "unit_amount": int(item.price * 100),
                    },
                    "quantity": item.qty,
                }
                for item in order.items.all()
            ],
            success_url=settings.FRONTEND_URL
            + f"/order/{order.pk}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=settings.FRONTEND_URL + "/cart",
            metadata={"order_id": str(order.pk)},
        )

        order.stripe_session_id = session.id
        order.save(update_fields=["stripe_session_id"])

        cart.items.all().delete()

        return Response({"order_id": order.pk, "checkout_url": session.url}, status=201)


def _finalize_order(order_id):
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)

        if order.status != "pending":
            return

        for item in order.items.select_related("product"):
            product = Product.objects.select_for_update().get(pk=item.product_id)
            if product.stock < item.qty:
                order.status = "cancelled"
                order.save(update_fields=["status"])
                return

            product.stock -= item.qty
            product.save(update_fields=["stock"])
            logger.info("finalize: product=%s stock_after=%s", product.id, product.stock)

        order.status = "paid"
        order.save(update_fields=["status"])
        logger.info("finalize: order %s marked paid", order_id)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig = request.META.get("HTTP_STRIPE_SIGNATURE")
    
    logger.info("Webhook received, sig presents: %s", bool(sig))
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.error("webhook signature check failed: %s", e)
        return HttpResponse(status=400)

    logger.info("webhook event type: %s", event["type"])


    if event["type"] == "checkout.session.completed":
        order_id = event["data"]["object"]["metadata"].get("order_id")

        if order_id:
            _finalize_order(order_id)

    return HttpResponse(status=200)
