from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product
from .services import ProductService


@receiver(post_save)
def product_stock_observer(sender, instance, **kwargs):
    """
    Імплементація патерну Observer

    Спостерігає за оновленнями продуктів та запускає сповіщення
    про низький рівень запасів через сервісний рівень
    """
    # Перевіряємо, чи є об'єкт екземпляром Product (або його підкласів FishingRod/Reel)
    if isinstance(instance, Product):
        ProductService.check_and_create_stock_alert(instance)
