from django.contrib import admin
from .models import (
    Product,
    FishingRod,
    Reel,
    StockAlert,
    Order,
    SubOrder,
    OrderItem,
)


@admin.register(FishingRod)
class FishingRodAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "stock",
        "length",
        "test_min",
        "test_max",
        "seller",
    )
    list_filter = ("material", "seller")
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
        "seller",
    )
    list_filter = ("seller",)
    search_fields = ("name", "description")


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "current_stock",
        "threshold",
        "status",
        "created_at",
        "product__seller",
    )
    list_filter = (
        "status",
        "created_at",
        "product__seller",
    )
    readonly_fields = ("product", "current_stock", "threshold", "created_at")


# Можемо зареєструвати базову модель, якщо потрібно
# додати товар із невизначеної категорії
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "stock",
        "low_stock_threshold",
        "updated_at",
        "seller",
    )
    search_fields = ("name",)


class OrderItemInline(admin.TabularInline):
    """Inline для відображення елементів замовлення в SubOrderAdmin."""

    model = OrderItem
    raw_id_fields = ["product"]
    readonly_fields = ("product_name", "price", "quantity", "total_price")
    extra = 0

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product")

    def total_price(self, obj):
        if obj.price is None:
            return "—"
        return obj.total_price

    total_price.short_description = "Загальна вартість"


class SubOrderInline(admin.StackedInline):
    """Inline для відображення підзамовлень в OrderAdmin."""

    model = SubOrder
    readonly_fields = ("seller", "status", "total_price", "created_at")
    extra = 0
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("seller")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Адмін-панель для головного замовлення."""

    list_display = ("id", "user", "total_price", "created_at")
    list_filter = ("created_at", "user")
    search_fields = ("id", "user__email", "user__username")
    readonly_fields = ("user", "total_price", "created_at", "updated_at")
    inlines = [SubOrderInline]


@admin.register(SubOrder)
class SubOrderAdmin(admin.ModelAdmin):
    """Адмін-панель для підзамовлення."""

    list_display = ("id", "order", "seller", "status", "total_price", "created_at")
    list_filter = ("status", "seller", "created_at")
    search_fields = ("id", "order__id", "seller__email")
    readonly_fields = ("order", "seller", "total_price", "created_at")
    inlines = [OrderItemInline]
    list_editable = ("status",)
