from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Кастомна модель користувача для рибацького магазину

    Може бути або користувачем, або покупцем
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "адміністратор"
        CUSTOMER = "CUSTOMER", "покупець"

    role = models.CharField(
        max_length=15,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name="Роль користувача",
    )

    def is_manager(self):
        """
        Перевірка на наявність дозволів адміна
        """
        return self.role == self.Role.ADMIN or self.is_superuser
