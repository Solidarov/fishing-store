from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .services import ProductService


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
