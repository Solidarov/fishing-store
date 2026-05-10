from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from store.services import ProductService


class ResolveAlertView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Вирішення сповіщення."""

    def test_func(self):
        return self.request.user.is_seller_member

    def post(self, request, pk):
        ProductService.resolve_alert(pk, request.user)
        return redirect("store:seller_dashboard")
