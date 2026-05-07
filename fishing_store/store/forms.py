from django import forms
from .models import Product, FishingRod, Reel


class ProductBaseForm(forms.ModelForm):
    """Базова форма для загальних товарів."""

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "stock",
            "low_stock_threshold",
            "image",
        ]


class FishingRodForm(forms.ModelForm):
    """Форма для створення та редагування вудок."""

    class Meta:
        model = FishingRod
        fields = [
            "name",
            "description",
            "price",
            "stock",
            "low_stock_threshold",
            "image",
            "length",
            "test_min",
            "test_max",
            "material",
        ]


class ReelForm(forms.ModelForm):
    """Форма для створення та редагування котушок."""

    class Meta:
        model = Reel
        fields = [
            "name",
            "description",
            "price",
            "stock",
            "low_stock_threshold",
            "image",
            "spool_size",
            "gear_ratio",
            "bearings_count",
        ]
