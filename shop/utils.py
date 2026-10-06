from shop.models import Cart
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes


CART_ID_PARAM = OpenApiParameter(
    name="X-Cart-Id",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.HEADER,
    required=False,
    description="Cart uuid from a previous response. Omit on first call to get a new cart"
)


def get_cart(request):
    cart_id = request.headers.get("X-Cart-Id") or request.query_params.get("cart_id")
    cart, _ = (
        Cart.objects.get_or_create(id=cart_id)
        if cart_id
        else (Cart.objects.create(), False)
    )
    return cart