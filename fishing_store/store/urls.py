from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    SellerDashboardView,
    ProductCreateView,
    ProductUpdateView,
    ProductDeleteView,
    ProductRestoreView,
    ResolveAlertView,
    cart_add,
    cart_remove,
    cart_clear,
    cart_detail,
)

app_name = "store"

urlpatterns = [
    path("", ProductListView.as_view(), name="product_list"),
    path("product/<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path("dashboard/", SellerDashboardView.as_view(), name="seller_dashboard"),
    path("product/add/", ProductCreateView.as_view(), name="product_add"),
    path("product/<int:pk>/edit/", ProductUpdateView.as_view(), name="product_edit"),
    path(
        "product/<int:pk>/delete/", ProductDeleteView.as_view(), name="product_delete"
    ),
    path(
        "product/<int:pk>/restore/",
        ProductRestoreView.as_view(),
        name="product_restore",
    ),
    path("alert/<int:pk>/resolve/", ResolveAlertView.as_view(), name="alert_resolve"),
    path("cart/", cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", cart_add, name="cart_add"),
    path("cart/remove/<int:product_id>/", cart_remove, name="cart_remove"),
    path("cart/clear/", cart_clear, name="cart_clear"),
]
