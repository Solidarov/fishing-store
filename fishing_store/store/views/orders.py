from django.views.generic import (
    ListView,
    View,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages

from store.services import CartService, OrderService
from store.models import SubOrder


class CheckoutView(LoginRequiredMixin, View):
    """Оформлення замовлення."""

    def post(self, request, *args, **kwargs):
        cart_service = CartService(request)
        if len(cart_service) == 0:
            messages.error(request, "Ваш кошик порожній.")
            return redirect("store:cart_detail")
        try:
            order = OrderService.create_order(request.user, cart_service)
            messages.success(
                request, f"Ваше замовлення №{order.id} було успішно створено!"
            )
            return redirect("store:order_history")
        except ValueError as e:
            messages.error(request, str(e))
            return redirect("store:cart_detail")


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
