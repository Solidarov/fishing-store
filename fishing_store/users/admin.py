from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ["username", "email", "role", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (("Додаткова інформація", {"fields": ("role",)}),)


admin.site.register(CustomUser, CustomUserAdmin)
