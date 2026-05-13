from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class UserSoftDeleteMixin(models.Model):
    """
    Міксин для реалізації "м'якого" видалення користувачів.
    Використовує існуюче поле is_active з AbstractUser.
    """

    deleted_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата видалення"
    )

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """М'яке видалення: встановлює дату видалення та деактивує користувача."""
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save()

    def hard_delete(self, *args, **kwargs):
        """Повне видалення об'єкта з бази даних."""
        super().delete(*args, **kwargs)

    def restore(self):
        """Відновлення м'яко видаленого користувача."""
        self.deleted_at = None
        self.is_active = True
        self.save()

    @property
    def is_deleted(self):
        """Перевіряє, чи був користувач видалений."""
        return self.deleted_at is not None


class CustomUser(UserSoftDeleteMixin, AbstractUser):
    """
    Кастомна модель користувача
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

    @property
    def is_admin_member(self):
        """Чи має користувач права адміна"""
        return self.is_superuser or self.role == self.Role.ADMIN

    @property
    def is_seller_member(self):
        """Чи має користувач права продавця"""
        return self.role == self.Role.SELLER

    @property
    def is_customer_member(self):
        """Чи має користувач права покупця"""
        return self.role == self.Role.CUSTOMER

    def save(self, *args, **kwargs):
        if self.is_superuser and self.role != self.Role.ADMIN:
            self.role = self.Role.ADMIN
        return super().save(*args, **kwargs)

    @property
    def display_name(self):
        """
        Повертає ім'я для відображення:
        - Назва магазину для продавців (якщо вказано)
        - Повне ім'я профілю (якщо вказано)
        - Юзернейм (як fallback)
        """
        if self.is_seller_member:
            try:
                if self.seller_profile.store_name:
                    return self.seller_profile.store_name
            except (AttributeError, SellerProfile.DoesNotExist):
                pass

        # Спроба взяти ім'я з профілю (Customer або Seller)
        profile = None
        if hasattr(self, "customer_profile"):
            profile = self.customer_profile
        elif hasattr(self, "seller_profile"):
            profile = self.seller_profile

        if profile and profile.first_name and profile.last_name:
            return f"{profile.first_name} {profile.last_name}"

        return self.username

    def __str__(self):
        """
        Стандартинй метод python для кращого представлення даних
        у терміналі / Django admin dashboard
        """
        return f"{self.username} ({self.get_role_display()})"


class BaseProfile(models.Model):
    """
    Базова модель профілю користувача.
    Додає базові поля до всіх моделей, що її наслідують
    """

    first_name = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Ім'я користувача"
    )
    last_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Прізвище користувача"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Номер телефону",
    )
    region = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Область",
    )
    city = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Місто",
    )
    street = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Назва вулиці",
    )
    house_num = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Номер будинку",
    )
    flat_num = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name="Номер квартири",
    )
    postal_code = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        verbose_name="Поштовий індекс",
    )

    class Meta:
        abstract = True


class CustomerProfile(BaseProfile):
    """
    Профіль покупця. Наслідує поля базового профілю
    """

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )

    def __str__(self):
        return f"Покупець: {self.user.username}"


class SellerProfile(BaseProfile):
    """
    Профіль продавця. Наслідує поля базового профілю
    """

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="seller_profile",
    )
    store_name = models.CharField(
        max_length=100,
        blank=True,
    )

    def __str__(self):
        return f"Продавець: {self.user.username}"
