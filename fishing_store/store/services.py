from decimal import Decimal
from .models import Product, StockAlert


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
        products = Product.objects.filter(id__in=product_ids, is_active=True)

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
