from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser, CustomerProfile, SellerProfile
from users.forms import CustomUserCreationForm, CustomUserChangeForm


class SoftDeleteModelAdmin(admin.ModelAdmin):
    actions = [
        "delete_queryset",
        "restore_model",
        "hard_delete_model",
    ]

    def get_actions(self, request):
        """Видаляємо стандартну дію видалення Django, щоб замінити її нашою"""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def delete_model(self, request, obj):
        """Переписує видалення однієї моделі (кнопка 'Delete' в картці)"""
        obj.delete()

    def delete_queryset(self, request, queryset):
        """Переписує масове видалення (через dropdown в списку)"""
        for obj in queryset:
            obj.delete()

    delete_queryset.short_description = "М'яко видалити вибрані записи"

    def restore_model(self, request, queryset):
        for obj in queryset:
            obj.restore()

    restore_model.short_description = "Відновити вибрані записи"

    def hard_delete_model(self, request, queryset):
        for obj in queryset:
            obj.hard_delete()

    hard_delete_model.short_description = "Повністю видалити вибрані записи"


class CustomerProfileInline(admin.StackedInline):
    """
    Інформація про профіль користувача
    """

    model = CustomerProfile
    can_delete = False
    verbose_name_plural = "Профіль покупця"


class SellerProfileInline(admin.StackedInline):
    """
    Інформація про профіль продавця
    """

    model = SellerProfile
    can_delete = False
    verbose_name_plural = "Профіль продавця"


class CustomUserAdmin(SoftDeleteModelAdmin, UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ["username", "email", "role", "is_active", "is_staff", "deleted_at"]
    list_filter = ["role", "is_active", "is_staff", "deleted_at"]

    fieldsets = UserAdmin.fieldsets + (
        ("Додаткова інформація", {"fields": ("role", "deleted_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "role", "password1", "password2"),
            },
        ),
    )

    def get_inline_instances(self, request, obj=None):
        """
        Отримання даних про профіль на основі моделі користувача.

        Працює тільки для ролей CUSTOMER та SELLER
        """
        if not obj:
            return list()

        inlines = []
        if obj.role == CustomUser.Role.CUSTOMER:
            inlines.append(CustomerProfileInline(self.model, self.admin_site))
        elif obj.role == CustomUser.Role.SELLER:
            inlines.append(SellerProfileInline(self.model, self.admin_site))

        return inlines


admin.site.register(CustomUser, CustomUserAdmin)
