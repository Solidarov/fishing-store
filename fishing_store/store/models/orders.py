from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from store.models import Product


class Order(models.Model):
    """
    Головна модель замовлення, що об'єднує підзамовлення.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Покупець",
    )
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Загальна вартість"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата оновлення")

    # Адресні дані
    first_name = models.CharField(max_length=50, verbose_name="Ім'я користувача")
    last_name = models.CharField(max_length=100, verbose_name="Прізвище користувача")
    phone_number = models.CharField(max_length=20, verbose_name="Номер телефону")
    region = models.CharField(max_length=50, verbose_name="Область")
    city = models.CharField(max_length=50, verbose_name="Місто")
    street = models.CharField(max_length=100, verbose_name="Вулиця")
    house_num = models.CharField(max_length=10, verbose_name="Номер будинку")
    flat_num = models.CharField(
        max_length=10, blank=True, verbose_name="Номер квартири"
    )
    postal_code = models.CharField(max_length=25, verbose_name="Поштовий індекс")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"

    def __str__(self):
        return f"Замовлення №{self.pk} від {self.user.username}"

    @property
    def can_be_canceled(self):
        """Перевіряє, чи є в замовленні підзамовлення, які ще можна скасувати (статус PENDING)."""
        return self.sub_orders.filter(status=SubOrder.Status.PENDING).exists()

    @property
    def effective_price(self):
        return sum(
            sub.total_price
            for sub in self.sub_orders.all()
            if sub.status != SubOrder.Status.CANCELED
        )

    @property
    def status(self):
        statuses = set(self.sub_orders.values_list("status", flat=True))
        active = statuses - {SubOrder.Status.CANCELED}

        if not statuses:
            return "empty"
        if not active:
            return SubOrder.Status.CANCELED.label

        if active == {SubOrder.Status.COMPLETED}:
            return SubOrder.Status.COMPLETED.label
        if active == {SubOrder.Status.PENDING}:
            return SubOrder.Status.PENDING.label
        if active == {SubOrder.Status.SENT}:
            return SubOrder.Status.SENT.label
        if SubOrder.Status.PENDING in active:
            return SubOrder.Status.PENDING.label  # є ще не оброблені продавцями

        return SubOrder.Status.SENT.label


class SubOrder(models.Model):
    """
    Підзамовлення, згруповане за продавцем.
    Реалізує патерн State через перевірку переходів статусів.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "В обробці"
        SENT = "SENT", "Відправлено"
        COMPLETED = "COMPLETED", "Завершено"
        CANCELED = "CANCELED", "Скасовано"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="sub_orders",
        verbose_name="Основне замовлення",
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sub_orders",
        verbose_name="Продавець",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус",
    )
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Вартість підзамовлення"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Підзамовлення"
        verbose_name_plural = "Підзамовлення"

    def __str__(self):
        return (
            f"Підзамовлення №{self.pk} для {self.seller.username}"
            f" ({self.get_status_display()})"
        )

    @property
    def delivery_address(self):
        """Повертає відформатовану адресу доставки з основного замовлення."""
        order = self.order
        address_parts = [
            order.postal_code,
            f"обл. {order.region}",
            f"м. {order.city}",
            f"{order.street}, буд. {order.house_num}",
        ]
        if order.flat_num:
            address_parts.append(f"кв. {order.flat_num}")

        return ", ".join(filter(None, address_parts))

    # State Pattern
    def can_mark_sent(self):
        """Перевіряє, чи можна змінити статус на 'Відправлено'."""
        return self.status == self.Status.PENDING

    def can_mark_completed(self):
        """Перевіряє, чи можна змінити статус на 'Завершено'."""
        return self.status == self.Status.SENT

    def can_cancel(self):
        """Перевіряє, чи можна скасувати підзамовлення."""
        return self.status in [self.Status.PENDING]

    def can_change_status(self):
        """Перевіряє, чи можна загалом змінити статус"""
        return self.can_mark_sent() or self.can_mark_sent() or self.can_cancel()

    def mark_sent(self):
        """Змінює статус на 'Відправлено'."""
        if not self.can_mark_sent():
            raise ValidationError(
                "Неможливо відправити замовлення, яке не знаходиться в обробці."
            )
        self.status = self.Status.SENT
        self.save()

    def mark_completed(self):
        """Змінює статус на 'Завершено'."""
        if not self.can_mark_completed():
            raise ValidationError(
                "Неможливо завершити замовлення, яке не було відправлено."
            )
        self.status = self.Status.COMPLETED
        self.save()

    def cancel(self):
        """Змінює статус на 'Скасовано'."""
        if not self.can_cancel():
            raise ValidationError(
                "Неможливо скасувати відправлене або завершене замовлення."
            )
        self.status = self.Status.CANCELED
        self.save()


class OrderItem(models.Model):
    """
    Елемент замовлення, що фіксує конкретний товар, його кількість та ціну.
    """

    sub_order = models.ForeignKey(
        SubOrder,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Підзамовлення",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_items",
        verbose_name="Товар",
    )
    # Зберігаємо копії даних на момент замовлення
    product_name = models.CharField(max_length=255, verbose_name="Назва товару")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Ціна на момент замовлення"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кількість")

    def __str__(self):
        return f"{self.quantity} x {self.product_name} у підзамовленні №{self.sub_order.pk}"

    @property
    def total_price(self):
        """Повертає загальну вартість для цього елемента."""
        return (self.price or Decimal("0")) * self.quantity
