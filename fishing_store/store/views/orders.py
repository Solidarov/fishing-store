from django.views.generic import ListView, View, FormView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages

from store.services import CartService, OrderService
from store.models import SubOrder
from store.forms import OrderCheckoutForm


class CheckoutView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """
    Оформлення замовлення: введення адреси та підтвердження.
    """

    template_name = "store/checkout.html"
    form_class = OrderCheckoutForm
    success_url = reverse_lazy("store:order_history")

    def test_func(self):
        # Чисті адміни без профілю не можуть робити замовлення
        if self.request.user.is_admin_member and not (
            hasattr(self.request.user, "customer_profile")
            or hasattr(self.request.user, "seller_profile")
        ):
            return False
        return True

    def handle_no_permission(self):
        messages.error(
            self.request,
            "Адміністратори не можуть створювати замовлення від свого імені.",
        )
        return redirect("store:product_list")

    def get_initial(self):
        """Передає дані з профілю користувача у форму."""
        user = self.request.user
        profile = getattr(user, "customer_profile", None) or getattr(
            user, "seller_profile", None
        )

        if profile:
            return {
                "phone_number": profile.phone_number,
                "region": profile.region,
                "city": profile.city,
                "street": profile.street,
                "house_num": profile.house_num,
                "flat_num": profile.flat_num,
                "postal_code": profile.postal_code,
            }
        return super().get_initial()

    def get(self, request, *args, **kwargs):
        """GET-запит: показуємо форму, перевіряємо кошик і роль."""
        cart_service = CartService(request)
        if len(cart_service) == 0:
            messages.warning(request, "Ваш кошик порожній.")
            return redirect("store:product_list")

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        """POST-запит, форма валідна: створюємо замовлення."""
        cart_service = CartService(self.request)
        checkout_data = form.cleaned_data.copy()
        save_to_profile = checkout_data.pop("save_to_profile", False)

        try:
            order = OrderService.create_order(
                user=self.request.user,
                cart_service=cart_service,
                checkout_data=checkout_data,
                save_to_profile=save_to_profile,
            )
            messages.success(
                self.request, f"Ваше замовлення №{order.id} успішно створено!"
            )
            return redirect(self.get_success_url())
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class CustomerOrderListView(LoginRequiredMixin, ListView):
    """
    Представлення для перегляду історії замовлень покупця.
    """

    template_name = "store/order_history.html"
    context_object_name = "orders"

    def get_queryset(self):
        return OrderService.get_customer_orders(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Додаткове сортування/групування можна зробити тут або в шаблоні
        # Для зручності передамо список замовлень як є, а в шаблоні розіб'ємо
        return context


class UpdateSubOrderStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Зміна статусу підзамовлення продавцем."""

    def test_func(self):
        # Перевіряємо, що користувач - продавець
        return self.request.user.is_seller_member

    def post(self, request, sub_order_id):
        new_status = request.POST.get("status")

        # Перевіряємо, чи є такий статус в моделі
        if new_status not in SubOrder.Status.values:
            messages.error(request, "Некоректний статус.")
            return redirect("store:seller_dashboard")

        try:
            OrderService.change_sub_order_status(sub_order_id, request.user, new_status)
            messages.success(request, f"Статус підзамовлення №{sub_order_id} оновлено.")
        except (ValueError, PermissionError) as e:
            messages.error(request, str(e))

        return redirect("store:seller_dashboard")


class CancelOrderView(LoginRequiredMixin, View):
    """Скасування замовлення покупцем."""

    http_method_names = ["post"]

    def post(self, request, order_id):
        try:
            OrderService.cancel_order(order_id, request.user)
            messages.success(request, f"Замовлення №{order_id} було скасовано.")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("store:order_history")
