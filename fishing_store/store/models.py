from django.db import models
from django.conf import settings


class Product(models.Model):
    """
    Базова модель Продукту, що використовує
    Мульти-табличне наслідування (Multi-table Inheritance, MTI)
    Містить базові поля для всіх типів рибацьких товарів
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold


class FishingRod(Product):
    """
    Окрема модель для Вудки

    Наслідує з моделі Product через MTI
    """

    length = models.FloatField(help_text="Length in meters")
    test_min = models.FloatField(help_text="Minimum test in grams")
    test_max = models.FloatField(help_text="Maximum test in grams")
    material = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Rod: {self.name} ({self.length}m)"


class Reel(Product):
    """
    Окрема модель для рибацької котушки

    Наслідує з моделі Product через MTI
    """

    spool_size = models.IntegerField(help_text="Size of the spool (e.g., 2000, 3000)")
    gear_ratio = models.CharField(max_length=20, help_text="e.g., 5.2:1")
    bearings_count = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Reel: {self.name} (Size {self.spool_size})"


class StockAlert(models.Model):
    """
    Модель логів для повідомлень про низьку кількість товарів

    Частина імплементації патерну Observer
    """

    STATUS_CHOICES = [
        ("NEW", "New"),
        ("RESOLVED", "Resolved"),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="stock_alerts"
    )
    current_stock = models.PositiveIntegerField()
    threshold = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NEW")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Alert: {self.product.name} (Stock: {self.current_stock})"
