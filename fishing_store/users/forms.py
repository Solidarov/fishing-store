from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from users.models import CustomUser, CustomerProfile, SellerProfile


class CustomUserCreationForm(UserCreationForm):
    """
    Форма для реєстрації нового користувача з вибором ролі.
    """

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email", "role")
        widgets = {
            "role": forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Виключаємо роль ADMIN та робимо вибір обов'язковим
        self.fields["role"].choices = [
            (choice_value, choice_label)
            for choice_value, choice_label in CustomUser.Role.choices
            if choice_value != CustomUser.Role.ADMIN
        ]

    def save(self, commit=True):
        user = super().save(commit=False)

        # активація продавців проводиться адміном
        if user.role == CustomUser.Role.SELLER:
            user.is_active = False
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    Технічна форма для Django Admin.
    """

    class Meta:
        model = CustomUser
        fields = ("username", "email", "role", "is_active")


class CustomUserUpdateForm(forms.ModelForm):
    """
    Форма для редагування базових даних користувача (для сторінки профілю).
    """

    class Meta:
        model = CustomUser
        fields = ("username", "email")


class CustomerProfileForm(forms.ModelForm):
    """
    Форма для редагування профілю покупця.
    """

    class Meta:
        model = CustomerProfile
        fields = (
            "first_name",
            "last_name",
            "phone_number",
            "region",
            "city",
            "street",
            "house_num",
            "flat_num",
            "postal_code",
        )


class SellerProfileForm(forms.ModelForm):
    """
    Форма для редагування профілю продавця.
    """

    class Meta:
        model = SellerProfile
        fields = (
            "store_name",
            "first_name",
            "last_name",
            "phone_number",
            "region",
            "city",
            "street",
            "house_num",
            "flat_num",
            "postal_code",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["store_name"].required = True
        self.fields["store_name"].help_text = "Назва вашого магазину, яку бачитимуть покупці"
