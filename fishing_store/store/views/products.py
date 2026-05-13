from django.views.generic import (
    ListView,
    DetailView,
    TemplateView,
    CreateView,
    UpdateView,
    View,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import Http404

from store.models import FishingRod, Reel
from store.services import ProductService, OrderService
from store.forms import FishingRodForm, ReelForm, ProductBaseForm, ProductFilterForm


class ProductListView(ListView):
    """Публічний каталог товарів з підтримкою пошуку та фільтрації."""

    template_name = "store/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        self.filter_form = ProductFilterForm(self.request.GET)
        if self.filter_form.is_valid():
            return ProductService.get_catalog_products(self.filter_form.cleaned_data)
        return ProductService.get_catalog_products()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context


class ProductDetailView(DetailView):
    """Деталі товару."""

    template_name = "store/product_detail.html"
    context_object_name = "product"

    def get_object(self, queryset=None):
        product = ProductService.get_product_by_id(self.kwargs.get("pk"))
        if product is None:
            raise Http404
        return product


class SellerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Панель керування продавця."""

    template_name = "store/seller_dashboard.html"

    def test_func(self):
        return self.request.user.is_seller_member

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["alerts"] = ProductService.get_active_alerts(user)
        context["products"] = ProductService.get_seller_products(user)
        context["sub_orders"] = OrderService.get_seller_orders(user)
        return context


class ProductCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Створення товару з авто-прив'язкою продавця."""

    template_name = "store/product_form.html"
    success_url = reverse_lazy("store:seller_dashboard")

    def test_func(self):
        return self.request.user.is_seller_member

    def get_form_class(self):
        product_type = self.request.GET.get("type")
        if product_type == "rod":
            return FishingRodForm
        elif product_type == "reel":
            return ReelForm
        return ProductBaseForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Додати новий товар"
        return context

    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редагування товару з перевіркою власності."""

    template_name = "store/product_form.html"
    success_url = reverse_lazy("store:seller_dashboard")

    def test_func(self):
        obj = self.get_object()
        if obj is None:
            return False
        return self.request.user.is_seller_member or obj.seller == self.request.user

    def get_object(self, queryset=None):
        return ProductService.get_product_by_id(
            self.kwargs.get("pk"), user=self.request.user
        )

    def get_form_class(self):
        obj = self.get_object()
        if isinstance(obj, FishingRod):
            return FishingRodForm
        elif isinstance(obj, Reel):
            return ReelForm
        return ProductBaseForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Редагування: {self.object.name}"
        return context


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """М'яке видалення товару."""

    def test_func(self):
        obj = ProductService.get_product_by_id(
            self.kwargs.get("pk"), user=self.request.user
        )
        if obj is None:
            return False
        return obj and (
            self.request.user.is_seller_member or obj.seller == self.request.user
        )

    def post(self, request, pk):
        hard = request.POST.get("hard") == "true"
        ProductService.delete_product(pk, request.user, hard=hard)
        return redirect("store:seller_dashboard")


class ProductRestoreView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Відновлення видаленого товару."""

    def test_func(self):
        return self.request.user.is_seller_member

    def post(self, request, pk):
        ProductService.restore_product(pk, request.user)
        return redirect("store:seller_dashboard")
