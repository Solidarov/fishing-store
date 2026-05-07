from django.contrib import admin
from .models import Product, FishingRod, Reel, StockAlert


@admin.register(FishingRod)
class FishingRodAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock", "length", "test_min", "test_max")
    list_filter = ("material",)
    search_fields = ("name", "description")


@admin.register(Reel)
class ReelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "stock",
        "spool_size",
        "gear_ratio",
        "bearings_count",
    )
    search_fields = ("name", "description")


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ("product", "current_stock", "threshold", "status", "created_at")
    list_filter = ("status", "created_at")
    readonly_fields = ("product", "current_stock", "threshold", "created_at")


# Можемо зареєструвати базову модель, якщо потрібно
# додати товар із невизначеної категорії
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock", "low_stock_threshold", "updated_at")
    search_fields = ("name",)
