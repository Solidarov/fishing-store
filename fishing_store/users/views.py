from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import (
    CustomUserCreationForm,
    CustomUserUpdateForm,
    CustomerProfileForm,
    SellerProfileForm,
)
from .models import CustomUser


class RegisterView(CreateView):
    """
    Клас для реєстрації нових користувачів.
    """

    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("profile")  # переадресація залогованого користувача
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        if user.is_active:
            # Користувач активний - логуємо його (Покупець)
            login(self.request, user)
            messages.success(
                self.request, f"Вітаємо, {user.username}! Реєстрація успішна."
            )
            return redirect("profile")
        else:
            # Користувач неактивний - залишаємо на сторінці логіну (Продавець)
            messages.info(
                self.request,
                "Ваш акаунт продавця створено. Будь ласка, зачекайте на активацію адміністратором.",
            )
            return redirect("login")


class UserLoginView(LoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("profile")


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("login")


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Відображення та редагування профілю користувача.
    """

    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["user_form"] = CustomUserUpdateForm(instance=user)

        # підтягуємо профіль з БД
        if user.role == CustomUser.Role.CUSTOMER and hasattr(user, "customer_profile"):
            context["profile_form"] = CustomerProfileForm(
                instance=user.customer_profile
            )
        elif user.role == CustomUser.Role.SELLER and hasattr(user, "seller_profile"):
            context["profile_form"] = SellerProfileForm(instance=user.seller_profile)
        else:
            context["profile_form"] = None

        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        user_form = CustomUserUpdateForm(request.POST, instance=user)

        # Визначення форми профілю (адмін не має форми)
        profile_form = None
        if user.role == CustomUser.Role.CUSTOMER and hasattr(user, "customer_profile"):
            profile_form = CustomerProfileForm(
                request.POST, instance=user.customer_profile
            )
        elif user.role == CustomUser.Role.SELLER and hasattr(user, "seller_profile"):
            profile_form = SellerProfileForm(request.POST, instance=user.seller_profile)

        is_user_valid = user_form.is_valid()
        is_profile_valid = profile_form.is_valid() if profile_form else True

        if is_user_valid and is_profile_valid:
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, "Ваш профіль успішно оновлено!")
            return redirect("profile")

        return render(
            request,
            self.template_name,
            {"user_form": user_form, "profile_form": profile_form},
        )
