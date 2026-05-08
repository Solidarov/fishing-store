from django.db import transaction
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
