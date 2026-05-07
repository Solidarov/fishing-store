from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    SellerDashboardView,
    ProductCreateView,
    ProductUpdateView,
    ResolveAlertView,
)

app_name = "store"

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path("product/<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path("dashboard/", SellerDashboardView.as_view(), name="seller_dashboard"),
    path("product/add/", ProductCreateView.as_view(), name="product_add"),
    path("product/<int:pk>/edit/", ProductUpdateView.as_view(), name="product_edit"),
    path("alert/<int:pk>/resolve/", ResolveAlertView.as_view(), name="alert_resolve"),
]
