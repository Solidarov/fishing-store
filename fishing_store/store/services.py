from django.db import transaction
from .models import Product, StockAlert


class ProductService:
    """
    Сервісний шар для бізнес логіки пов'язаної з продуктами

    Забезпечує Single Responsibility Principle тим,
    що відділяє логіку та операції з БД від views
    """

    @staticmethod
    def get_all_products():
        """Повертає всі продукти відсортовані за датою створення"""
        return Product.objects.all().order_by("-created_at")

    @staticmethod
    def get_product_by_id(product_id):
        """Отримує специфічний товар або об'єкт його підкласу (напр, вудка або котушка)"""
        try:
            product = Product.objects.get(id=product_id)
            # Django MTI: спробуємо повернути найбільш конкретний екземпляр
            if hasattr(product, "fishingrod"):
                return product.fishingrod
            if hasattr(product, "reel"):
                return product.reel
            return product
        except Product.DoesNotExist:
            return None

    @staticmethod
    def check_and_create_stock_alert(product):
        """
        Логіка для перевірки чи товару на складі не замало та створити повідомлення

        Використовується для Observer (Signals)
        """
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
            # Якщо запас достатній (> порогу), закриваємо всі нові сповіщення для цього товару
            StockAlert.objects.filter(product=product, status="NEW").update(
                status="RESOLVED"
            )

    @staticmethod
    def resolve_alert(alert_id):
        """Позначає конкретне сповіщення як вирішене (ручне керування)."""
        alert = StockAlert.objects.filter(id=alert_id).first()
        if alert:
            alert.status = "RESOLVED"
            alert.save()
            return True
        return False

    @staticmethod
    def get_active_alerts():
        """Повертає всі активні логи про критично низьку кількість товару"""
        return StockAlert.objects.filter(status="NEW").select_related("product")
