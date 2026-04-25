from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Кастомна модель користувача для рибацького магазину.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Адміністратор"
        SELLER = "SELLER", "Продавець"
        CUSTOMER = "CUSTOMER", "Покупець"

    role = models.CharField(
        max_length=15,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name="Роль користувача",
    )

    phone_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Номер телефону"
    )

    address = models.TextField(blank=True, null=True, verbose_name="Адреса доставки")

    @property
    def is_admin_member(self):
        """Чи має користувач права адміна"""
        return self.is_superuser or self.role == self.Role.ADMIN

    @property
    def is_seller_member(self):
        """Чи має користувач права продавця"""
        return self.role == self.Role.SELLER or self.is_admin_member

    @property
    def is_customer_member(self):
        """Чи має користувач права покупця"""
        return self.role == self.Role.CUSTOMER

    def save(self, *args, **kwargs):
        if self.is_superuser and self.role != self.Role.ADMIN:
            self.role = self.Role.ADMIN
        return super().save(*args, **kwargs)

    def __str__(self):
        """
        Стандартинй метод python для кращого представлення даних
        у терміналі / Django admin dashboard
        """
        return f"{self.username} ({self.get_role_display()})"
