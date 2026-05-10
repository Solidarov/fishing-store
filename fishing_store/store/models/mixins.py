from django.db import models
from django.utils import timezone


class SoftDeleteMixin(models.Model):
    """
    Міксин для реалізації "м'якого" видалення об'єктів.
    Додає поля для відстеження видалення та деактивації.
    """

    deleted_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата видалення"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активний")

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        """М'яке видалення: встановлює дату видалення та деактивує об'єкт."""
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save()

    def hard_delete(self, *args, **kwargs):
        """Повне видалення об'єкта з бази даних."""
        super().delete(*args, **kwargs)

    def restore(self):
        """Відновлення м'яко видаленого об'єкта."""
        self.deleted_at = None
        self.is_active = True
        self.save()

    @property
    def is_deleted(self):
        """Перевіряє, чи був об'єкт видалений."""
        return self.deleted_at is not None
