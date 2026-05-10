from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser, CustomerProfile, SellerProfile
from users.forms import CustomUserCreationForm, CustomUserChangeForm


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


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ["username", "email", "role", "is_active", "is_staff"]
    list_filter = ["role", "is_active", "is_staff"]

    fieldsets = UserAdmin.fieldsets + (("Додаткова інформація", {"fields": ("role",)}),)
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
