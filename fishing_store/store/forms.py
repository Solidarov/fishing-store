from django import forms
from store.models import Product, FishingRod, Reel, Order


class OrderCheckoutForm(forms.ModelForm):
    """Форма для оформлення замовлення та введення адреси доставки."""

    save_to_profile = forms.BooleanField(
        label="Зберегти адресу для майбутніх замовлень?", required=False, initial=True
    )

    class Meta:
        model = Order
        fields = [
            "phone_number",
            "region",

            "city",
            "street",
            "house_num",
            "flat_num",
            "postal_code",
        ]
        labels = {
            "phone_number": "Номер телефону",
            "region": "Область",
            "city": "Місто/Село",
            "street": "Вулиця",
            "house_num": "Номер будинку",
            "flat_num": "Номер квартири (необов'язково)",
            "postal_code": "Поштовий індекс",
        }


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
