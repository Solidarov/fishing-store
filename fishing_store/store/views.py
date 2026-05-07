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
from .models import Product, FishingRod, Reel, StockAlert
from .services import ProductService
from .forms import FishingRodForm, ReelForm, ProductBaseForm


class ProductListView(ListView):
    """
    Відображає каталог продуктів

    Використовує сервісний шар для отримання даних з БД (SPR)
    """

    template_name = "store/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        return ProductService.get_all_products()


class ProductDetailView(DetailView):
    """
    Відображає детальну інформацю про продукт, включно з полями, характерними для підкласів.
    """

    template_name = "store/product_detail.html"
    context_object_name = "product"

    def get_object(self, queryset=None):
        return ProductService.get_product_by_id(self.kwargs.get("pk"))


class SellerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Панель управління для продавців, що дозволяє керувати товарами
    та переглядати сповіщення про стан запасів.
    """

    template_name = "store/seller_dashboard.html"

    def test_func(self):
        return self.request.user.is_seller_member or self.request.user.is_admin_member

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["alerts"] = ProductService.get_active_alerts()
        context["products"] = ProductService.get_all_products()
        return context


class ProductCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Створення нового товару. Тип товару визначається через параметр у URL (type).
    """

    template_name = "store/product_form.html"
    success_url = reverse_lazy("store:seller_dashboard")

    def test_func(self):
        return self.request.user.is_seller_member

    def get_form_class(self):
        # Отримуємо параметр type через URL, для вибору потрібної форми
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


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Редагування існуючого товару. Автоматично підбирає потрібну форму для підкласу.
    """

    template_name = "store/product_form.html"
    success_url = reverse_lazy("store:seller_dashboard")

    def test_func(self):
        return self.request.user.is_seller_member

    def get_object(self, queryset=None):
        return ProductService.get_product_by_id(self.kwargs.get("pk"))

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


class ResolveAlertView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Ручне закриття сповіщення про низький запас.
    """

    def test_func(self):
        return self.request.user.is_seller_member

    def post(self, request, pk):
        ProductService.resolve_alert(pk)
        return redirect("store:seller_dashboard")
