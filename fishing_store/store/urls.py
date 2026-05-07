from django.urls import path
from .views import ProductListView, ProductDetailView, SellerDashboardView

app_name = 'store'

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('dashboard/', SellerDashboardView.as_view(), name='seller_dashboard'),
]
