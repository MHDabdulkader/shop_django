from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from shop.models import Product


class Command(BaseCommand):
    help = "Create tester user + 3 products with known stock"

    def handle(self, *args, **opts):
        u, _ = get_user_model().objects.get_or_create(username="tester")
        u.set_password("pass12345")
        u.save()
        for name, price in [("A", 10), ("B", 20), ("C", 30)]:
            Product.objects.update_or_create(
                name=name, defaults={"owner": u, "price": price, "stock": 5}
            )
        self.stdout.write("seeded: tester / pass12345")