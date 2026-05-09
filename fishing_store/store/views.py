from django.views.generic import (
    ListView,
    DetailView,
    TemplateView,
    CreateView,
    UpdateView,
    View,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.http import Http404
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Product, FishingRod, Reel
from .services import ProductService, CartService
from .forms import FishingRodForm, ReelForm, ProductBaseForm


class ProductListView(ListView):
    """Публічний каталог товарів."""

    template_name = "store/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        return ProductService.get_catalog_products()


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
        context["alerts"] = ProductService.get_active_alerts(self.request.user)
        context["products"] = ProductService.get_seller_products(self.request.user)
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
            self.request.user.is_admin_member or obj.seller == self.request.user
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


class ResolveAlertView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Вирішення сповіщення."""

    def test_func(self):
        return self.request.user.is_seller_member

    def post(self, request, pk):
        ProductService.resolve_alert(pk, request.user)
        return redirect("store:seller_dashboard")


@require_POST
def cart_add(request, product_id):
    """Додавання товару в кошик."""
    cart = CartService(request)
    product = get_object_or_404(Product, id=product_id)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1

    try:
        cart.add(product=product, quantity=quantity, override_quantity=False)
        messages.success(request, f'"{product.name}" додано до кошика.')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect("store:product_detail", pk=product_id)


def cart_remove(request, product_id):
    """Видалення товару з кошика."""
    cart = CartService(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f'"{product.name}" видалено з кошика.')
    return redirect("store:cart_detail")


def cart_clear(request):
    """Повне очищення кошика."""
    cart = CartService(request)
    cart.clear()
    messages.info(request, "Ваш кошик було очищено.")
    return redirect("store:cart_detail")


def cart_detail(request):
    """Відображення сторінки кошика."""
    return render(request, "store/cart_detail.html")
