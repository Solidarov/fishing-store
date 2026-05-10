from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from collections import defaultdict

from .models import (
    Product,
    StockAlert,
    Order,
    SubOrder,
    OrderItem,
)


class ProductService:
    """
    Сервісний шар для бізнес логіки пов'язаної з продуктами

    Забезпечує Single Responsibility Principle тим,
    що відділяє логіку та операції з БД від views
    """

    @staticmethod
    def get_catalog_products():
        """Повертає товари для публічного каталогу (не видалені та активні)."""
        return Product.objects.filter(deleted_at__isnull=True, is_active=True).order_by(
            "-created_at"
        )

    @staticmethod
    def get_seller_products(user):
        """Повертає товари конкретного продавця (включаючи м'яко видалені для керування)."""
        return Product.objects.filter(seller=user).order_by("-created_at")

    @staticmethod
    def get_product_by_id(product_id, user=None):
        """Отримує товар з перевіркою прав доступу, якщо вказано user."""
        try:
            product = Product.objects.get(id=product_id)

            # Якщо передано користувача, перевіряємо чи він має право бачити цей товар (власник або адмін)
            # Це важливо для редагування/видалення
            if user and not user.is_admin_member and product.seller != user:
                return None

            # Повертаємо найбільш специфічний екземпляр
            if hasattr(product, "fishingrod"):
                return product.fishingrod
            if hasattr(product, "reel"):
                return product.reel
            return product
        except Product.DoesNotExist:
            return None

    @staticmethod
    def delete_product(product_id, user, hard=False):
        """Видаляє товар (м'яко або повністю)."""
        product = ProductService.get_product_by_id(product_id, user)
        if product:
            if hard:
                product.hard_delete()
            else:
                product.delete()
            return True
        return False

    @staticmethod
    def restore_product(product_id, user):
        """Відновлює м'яко видалений товар."""
        product = Product.objects.filter(id=product_id).first()
        if product and (user.is_admin_member or product.seller == user):
            product.restore()
            return True
        return False

    @staticmethod
    def check_and_create_stock_alert(product):
        """Логіка перевірки залишків та авто-вирішення алертів."""
        if product.is_low_stock():
            # Створити сповіщення тільки якщо не існує активного запису для цієї кількості товару
            # щоб не спамити логами після кожного маленького оновлення
            StockAlert.objects.update_or_create(
                product=product,
                status="NEW",
                defaults={
                    "current_stock": product.stock,
                    "threshold": product.low_stock_threshold,
                },
            )
        else:
            StockAlert.objects.filter(product=product, status="NEW").update(
                status="RESOLVED"
            )

    @staticmethod
    def get_active_alerts(user):
        """Повертає алерти, фільтруючи їх через власника товару."""
        queryset = StockAlert.objects.filter(
            status="NEW", product__seller=user
        ).select_related("product")
        return queryset

    @staticmethod
    def resolve_alert(alert_id, user):
        """Ручне закриття сповіщення з перевіркою прав."""
        alert = StockAlert.objects.filter(id=alert_id).select_related("product").first()
        if alert and (user.is_admin_member or alert.product.seller == user):
            alert.status = "RESOLVED"
            alert.save()
            return True
        return False


class CartService:
    """
    Сервісний шар для керування кошиком покупок, що зберігається в сесії.
    """

    CART_SESSION_ID = "cart"

    def __init__(self, request):
        """Ініціалізує сервіс кошика, отримуючи доступ до сесії."""
        self.session = request.session
        cart = self.session.get(self.CART_SESSION_ID)
        if not cart:
            cart = self.session[self.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Додає товар до кошика або оновлює його кількість.
        Виконує перевірку наявності товару та залишків на складі.
        """
        if not product.is_available:
            raise ValueError("Цей товар недоступний для покупки.")

        product_id = str(product.id)
        current_quantity = self.cart.get(product_id, {}).get("quantity", 0)

        if override_quantity:
            new_quantity = quantity
        else:
            new_quantity = current_quantity + quantity

        if product.stock < new_quantity:
            raise ValueError(f"На складі є лише {product.stock} одиниць цього товару.")

        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0, "price": str(product.price)}

        self.cart[product_id]["quantity"] = new_quantity
        self.save()

    def remove(self, product):
        """Видаляє товар з кошика."""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Ітерує по товарах у кошику, додаючи до них об'єкти Product.
        Це дозволяє отримати повну інформацію про товар у шаблонах.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(
            id__in=product_ids, is_active=True
        ).select_related("seller")

        cart = self.cart.copy()
        for product in products:
            if product.is_available:  # Додаткова перевірка
                cart[str(product.id)]["product"] = product

        for item in cart.values():
            if "product" in item:
                item["price"] = Decimal(item["price"])
                item["total_price"] = item["price"] * item["quantity"]
                yield item

    def __len__(self):
        """Повертає загальну кількість товарів у кошику."""
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        """Обчислює загальну вартість всіх товарів у кошику."""
        return sum(
            Decimal(item["price"]) * item["quantity"] for item in self.cart.values()
        )

    def clear(self):
        """Повністю очищує кошик."""
        if self.CART_SESSION_ID in self.session:
            del self.session[self.CART_SESSION_ID]
            self.save()

    def save(self):
        """Зберігає зміни в сесії."""
        self.session.modified = True


class OrderService:
    """
    Сервісний шар для бізнес-логіки, пов'язаної із замовленнями.
    Реалізує патерн Facade для процесу оформлення замовлення.
    """

    @staticmethod
    def create_order(user, cart_service: CartService):
        """
        Створює замовлення з товарів у кошику.
        - Створює `Order` та `SubOrder` для кожного продавця.
        - Зменшує залишки на складі.
        - Очищує кошик.
        Все виконується в атомній транзакції.
        """
        if len(cart_service) == 0:
            raise ValueError("Кошик порожній, неможливо створити замовлення.")

        all_cart_items = list(cart_service)

        # Швидка перевірка наявності достатньої к-сті товару (для UI, не гарантовано)
        for item in all_cart_items:
            product = item["product"]
            if product.stock < item["quantity"]:
                raise ValueError(f"Недостатньо товару '{product.name}' на складі.")

        with transaction.atomic():
            # 1. Зарезервувати продукти, що в кошику для транзакції
            products = Product.objects.select_for_update().filter(
                pk__in=[item["product"].pk for item in all_cart_items]
            )

            # 2. Повторна перевірка товару вже з блокуванням (гарантована)
            quantity_by_pk = {
                item["product"].pk: item["quantity"] for item in all_cart_items
            }
            for product in products:
                if product.stock < quantity_by_pk[product.pk]:
                    raise ValueError(f"Недостатньо товару '{product.name}' на складі.")

            # 3. Створити головне замовлення
            order = Order.objects.create(
                user=user, total_price=cart_service.get_total_price()
            )

            # 4. Згрупувати товари в кошику за продавцем
            items_by_seller = defaultdict(list)
            for item in all_cart_items:
                items_by_seller[item["product"].seller].append(item)

            # 5. Створити підзамовлення для кожного продавця
            order_items_to_create = []

            for seller, items in items_by_seller.items():
                sub_order_total = sum(item["total_price"] for item in items)
                sub_order = SubOrder.objects.create(
                    order=order, seller=seller, total_price=sub_order_total
                )

                # 6. Створити елементи замовлення
                for item in items:
                    product = item["product"]
                    quantity = item["quantity"]

                    order_items_to_create.append(
                        OrderItem(
                            sub_order=sub_order,
                            product=product,
                            product_name=product.name,
                            price=product.price,
                            quantity=quantity,
                        )
                    )

            OrderItem.objects.bulk_create(order_items_to_create)

            # 7. Оновити склад
            for product in products:
                product.stock = F("stock") - quantity_by_pk[product.pk]

            Product.objects.bulk_update(products, ["stock"])

        # 8. Очистити кошик після успішної транзакції
        cart_service.clear()
        return order

    @staticmethod
    def change_sub_order_status(sub_order_id, user, new_status):
        """
        Змінює статус підзамовлення з перевіркою прав доступу та логіки стану.
        Якщо статус змінюється на 'Canceled', товари повертаються на склад.
        """
        try:
            sub_order = SubOrder.objects.get(pk=sub_order_id)
        except SubOrder.DoesNotExist:
            raise ValueError("Підзамовлення не знайдено.")

        # Перевірка прав: тільки продавець цього підзамовлення або адмін
        if not (user.is_admin_member or sub_order.seller == user):
            raise PermissionError("У вас немає прав на зміну цього підзамовлення.")

        try:
            if new_status == SubOrder.Status.SENT:
                sub_order.mark_sent()
            elif new_status == SubOrder.Status.COMPLETED:
                sub_order.mark_completed()
            elif new_status == SubOrder.Status.CANCELED:
                OrderService._perform_sub_order_cancellation(sub_order)
            else:
                raise ValueError(f"Невідомий статус: {new_status}")
        except ValidationError as e:
            raise ValueError(e.message)

        return sub_order

    @staticmethod
    def _perform_sub_order_cancellation(sub_order):
        """Внутрішній метод для технічного виконання скасування та повернення товарів."""
        with transaction.atomic():
            sub_order.cancel()
            items_to_update = []
            # Повернення товарів на склад за допомогою атомарних операцій
            for item in sub_order.items.all():
                if item.product:
                    item.product.stock = F("stock") + item.quantity
                    items_to_update.append(item.product)
            Product.objects.bulk_update(items_to_update, ["stock"])

    @staticmethod
    @transaction.atomic
    def cancel_order(order_id, user):
        """
        Скасовує замовлення покупцем.
        Скасовуються тільки ті підзамовлення, які ще в статусі PENDING.
        """
        try:
            order = Order.objects.get(pk=order_id, user=user)
        except Order.DoesNotExist:
            raise ValueError("Замовлення не знайдено.")

        sub_orders_to_cancel = order.sub_orders.filter(status=SubOrder.Status.PENDING)

        if not sub_orders_to_cancel.exists():
            raise ValueError(
                "Це замовлення неможливо скасувати (усі товари вже відправлені або завершені)."
            )

        for sub_order in sub_orders_to_cancel:
            OrderService._perform_sub_order_cancellation(sub_order)

        return True

    @staticmethod
    def get_customer_orders(user):
        """
        Повертає всі замовлення для покупця, посортовані за датою.
        У шаблоні ми зможемо додатково групувати або сортувати за статусом підзамовлень.
        """
        return (
            Order.objects.filter(user=user)
            .prefetch_related("sub_orders__items__product", "sub_orders__seller")
            .order_by("-created_at")
        )

    @staticmethod
    def get_seller_orders(user):
        """Повертає всі підзамовлення для вказаного продавця."""
        return (
            SubOrder.objects.filter(seller=user)
            .prefetch_related("items__product")
            .order_by("-created_at")
        )
