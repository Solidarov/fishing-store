from django.core.management.base import BaseCommand
from fishing_store.settings import DJANGO_SUPERUSER_PASSWORD
from store.models import Product, FishingRod, Reel
from users.models import CustomUser


class Command(BaseCommand):
    help = "Seeds the database with initial test data"

    def handle(self, *args, **options):
        sellers = self.create_init_sellers()
        self.create_init_customer()
        for seller in sellers:
            self.create_all_kinds_products_to_seller(seller)
        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))

    def create_init_sellers(self):
        """Створення базових продавців та їхня активація"""

        init_sellers = []
        sellers_data = [
            {
                "username": "basic_seller1",
                "role": CustomUser.Role.SELLER,
                "defaults": {"email": "seller1@example.com"},
            },
            {
                "username": "basic_seller2",
                "role": CustomUser.Role.SELLER,
                "defaults": {"email": "seller2@example.com"},
            },
            {
                "username": "basic_seller3",
                "role": CustomUser.Role.SELLER,
                "defaults": {"email": "seller3@example.com"},
            },
        ]

        for data in sellers_data:
            defaults = data.pop("defaults")
            seller, created = CustomUser.objects.get_or_create(
                **data,
                defaults=defaults,
            )

            if created:
                seller.set_password(DJANGO_SUPERUSER_PASSWORD)
            seller.is_active = True
            seller.save()

            init_sellers.append(seller)

        self.stdout.write(f"    Successfully added {len(sellers_data)} basic sellers")
        return init_sellers

    def create_init_customer(self):
        """Створення базового покупця"""

        customer, created = CustomUser.objects.get_or_create(
            username="basic_customer",
            role=CustomUser.Role.CUSTOMER,
            defaults={
                "email": "customer@example.com",
            },
        )

        if created:
            customer.set_password(DJANGO_SUPERUSER_PASSWORD)
        customer.save()

        self.stdout.write("    Successfully added 1 basic customer")

    def create_all_kinds_products_to_seller(self, seller):

        name = f"{seller.username}'s {Product._meta.verbose_name}"
        Product.objects.get_or_create(
            name=name, seller=seller, defaults={"price": 125, "stock": 50}
        )

        name = f"{seller.username}'s {FishingRod._meta.verbose_name}"
        FishingRod.objects.get_or_create(
            name=name,
            seller=seller,
            defaults={
                "price": 125,
                "stock": 50,
                "length": 15,
                "test_min": 1,
                "test_max": 500,
            },
        )

        name = f"{seller.username}'s {Reel._meta.verbose_name}"
        Reel.objects.get_or_create(
            name=name,
            seller=seller,
            defaults={
                "price": 125,
                "stock": 50,
                "spool_size": 2000,
                "gear_ratio": "5.2:1",
            },
        )

        self.stdout.write(
            f"    Successfully added all basic items to {seller.username}"
        )
