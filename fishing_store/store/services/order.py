from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from collections import defaultdict

from store.services import CartService

from store.models import (
    Product,
    Order,
    SubOrder,
    OrderItem,
)


class OrderService:
    """
    Сервісний шар для бізнес-логіки, пов'язаної із замовленнями.
    Реалізує патерн Facade для процесу оформлення замовлення.
    """

    @staticmethod
    def create_order(
        user, cart_service: CartService, checkout_data: dict, save_to_profile: bool
    ):
        """
        Створює замовлення з товарів у кошику.
        - Зберігає адресу доставки в `Order`.
        - Опціонально оновлює профіль користувача.
        - Створює `SubOrder` для кожного продавця.
        - Зменшує залишки на складі.
        - Очищує кошик.
        Все виконується в атомній транзакції.
        """
        if len(cart_service) == 0:
            raise ValueError("Кошик порожній, неможливо створити замовлення.")

        all_cart_items = list(cart_service)

        # 1. Попередня перевірка залишків
        OrderService._check_initial_stock(all_cart_items)

        with transaction.atomic():
            # 2. Блокування товарів та фінальна перевірка
            products = OrderService._lock_and_verify_stock(all_cart_items)

            # 3. Створити головне замовлення
            order = OrderService._create_main_order(user, cart_service, checkout_data)

            # 4. Створити підзамовлення та елементи замовлення
            OrderService._create_sub_orders_and_items(order, all_cart_items)

            # 5. Оновити склад
            OrderService._deduct_stock(products, all_cart_items)

            # 6. Оновити профіль користувача за потреби
            if save_to_profile:
                OrderService._update_user_profile(user, checkout_data)

        # 7. Очистити кошик після успішної транзакції
        cart_service.clear()
        return order

    @staticmethod
    def _check_initial_stock(cart_items):
        """Швидка перевірка наявності достатньої к-сті товару (для UI)."""
        for item in cart_items:
            product = item["product"]
            if product.stock < item["quantity"]:
                raise ValueError(f"Недостатньо товару '{product.name}' на складі.")

    @staticmethod
    def _lock_and_verify_stock(cart_items):
        """Зарезервувати продукти та провести гарантовану перевірку залишків."""
        products_pks = [item["product"].pk for item in cart_items]
        products = Product.objects.select_for_update().filter(pk__in=products_pks)

        quantity_by_pk = {item["product"].pk: item["quantity"] for item in cart_items}
        for product in products:
            if product.stock < quantity_by_pk[product.pk]:
                raise ValueError(f"Недостатньо товару '{product.name}' на складі.")
        return products

    @staticmethod
    def _create_main_order(user, cart_service, checkout_data):
        """Створити головне замовлення з даними з форми."""
        order_data = {
            "user": user,
            "total_price": cart_service.get_total_price(),
            **checkout_data,
        }
        return Order.objects.create(**order_data)

    @staticmethod
    def _create_sub_orders_and_items(order, cart_items):
        """Групує товари за продавцем та створює підзамовлення та їх елементи."""
        items_by_seller = defaultdict(list)
        for item in cart_items:
            items_by_seller[item["product"].seller].append(item)

        order_items_to_create = []

        for seller, items in items_by_seller.items():
            sub_order_total = sum(item["total_price"] for item in items)
            sub_order = SubOrder.objects.create(
                order=order, seller=seller, total_price=sub_order_total
            )

            for item in items:
                product = item["product"]
                order_items_to_create.append(
                    OrderItem(
                        sub_order=sub_order,
                        product=product,
                        product_name=product.name,
                        price=product.price,
                        quantity=item["quantity"],
                    )
                )

        OrderItem.objects.bulk_create(order_items_to_create)

    @staticmethod
    def _deduct_stock(products, cart_items):
        """Атомарне зменшення залишків на складі."""
        quantity_by_pk = {item["product"].pk: item["quantity"] for item in cart_items}
        for product in products:
            product.stock = F("stock") - quantity_by_pk[product.pk]

        Product.objects.bulk_update(products, ["stock"])

    @staticmethod
    def _update_user_profile(user, checkout_data):
        """Оновлює профіль користувача новими даними адреси."""
        profile = getattr(user, "customer_profile", None) or getattr(
            user, "seller_profile", None
        )
        if profile:
            for field, value in checkout_data.items():
                if hasattr(profile, field):
                    setattr(profile, field, value)
            profile.save()

    @staticmethod
    def change_sub_order_status(sub_order_id, user, new_status):
        """
        Змінює статус підзамовлення з перевіркою прав доступу та логіки стану.
        Якщо статус змінюється на 'Canceled', товари повертаються на склад.
        """
        try:
            sub_order = SubOrder.objects.select_related("seller").get(pk=sub_order_id)
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
            for item in sub_order.items.select_related("product").all():
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
            .select_related("order__user")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )
