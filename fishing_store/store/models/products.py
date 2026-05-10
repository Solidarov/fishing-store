from django.db import models
from django.conf import settings
from django.urls import reverse
from store.models import SoftDeleteMixin


class Product(SoftDeleteMixin, models.Model):
    """
    Базова модель товару з використанням Multi-table inheritance та Soft Delete.
    """

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Продавець",
    )
    name = models.CharField(max_length=255, verbose_name="Назва")
    description = models.TextField(blank=True, verbose_name="Опис")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    stock = models.PositiveIntegerField(default=0, verbose_name="Кількість на складі")
    low_stock_threshold = models.PositiveIntegerField(
        default=5, verbose_name="Поріг низького запасу"
    )
    image = models.ImageField(
        upload_to="products/", blank=True, null=True, verbose_name="Зображення"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата оновлення")

    class Meta:
        verbose_name = "Рибацький товар"
        verbose_name_plural = "Рибацькі товари"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Повертає канонічну URL-адресу для екземпляра продукту."""
        return reverse("store:product_detail", kwargs={"pk": self.pk})

    def is_low_stock(self):
        """Перевіряє, чи є запас нижчим за встановлений поріг."""
        return self.stock <= self.low_stock_threshold

    @property
    def is_available(self):
        """
        Перевіряє доступність товару:
        не видалений, активний та є в наявності на складі.
        """
        return not self.is_deleted and self.is_active and self.stock > 0

    @property
    def can_be_viewed(self):
        """Товар можна переглядати, якщо він не видалений та активний."""
        return not self.is_deleted and self.is_active


class FishingRod(Product):
    """
    Окрема модель для Вудки

    Наслідує з моделі Product через MTI
    """

    length = models.FloatField(help_text="Довжина в метрах", verbose_name="Довжина")
    test_min = models.FloatField(
        help_text="Мінімальний тест у грамах", verbose_name="Тест (мін)"
    )
    test_max = models.FloatField(
        help_text="Максимальний тест у грамах", verbose_name="Тест (макс)"
    )
    material = models.CharField(max_length=100, blank=True, verbose_name="Матеріал")

    class Meta:
        verbose_name = "Рибацька вудка"
        verbose_name_plural = "Рибацькі вудки"

    def __str__(self):
        return f"Вудлище: {self.name} ({self.length}м)"


class Reel(Product):
    """
    Окрема модель для рибацької котушки

    Наслідує з моделі Product через MTI
    """

    spool_size = models.IntegerField(
        help_text="Розмір шпулі (наприклад, 2000, 3000)", verbose_name="Розмір шпулі"
    )
    gear_ratio = models.CharField(
        max_length=20, help_text="Наприклад, 5.2:1", verbose_name="Передавальне число"
    )
    bearings_count = models.PositiveIntegerField(
        default=1, verbose_name="Кількість підшипників"
    )

    class Meta:
        verbose_name = "Рибацька котушка"
        verbose_name_plural = "Рибацькі котушки"

    def __str__(self):
        return f"Котушка: {self.name} (Розмір {self.spool_size})"
