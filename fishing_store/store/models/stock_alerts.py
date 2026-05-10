from django.db import models
from store.models import Product


class StockAlert(models.Model):
    """
    Модель логів для повідомлень про низьку кількість товарів

    Частина імплементації патерну Observer
    """

    STATUS_CHOICES = [
        ("NEW", "Нове"),
        ("RESOLVED", "Вирішено"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stock_alerts",
        verbose_name="Товар",
    )
    current_stock = models.PositiveIntegerField(verbose_name="Поточний запас")
    threshold = models.PositiveIntegerField(verbose_name="Поріг")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="NEW", verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата виникнення")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Сповіщення про запас"
        verbose_name_plural = "Сповіщення про запаси"

    def __str__(self):
        return f"Сповіщення: {self.product.name} (Запас: {self.current_stock})"
