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


class ProductFilterForm(forms.Form):
    """Форма для фільтрації та пошуку товарів у каталозі."""

    search = forms.CharField(
        required=False,
        label="Пошук",
        widget=forms.TextInput(attrs={"placeholder": "Назва або опис..."}),
    )
    category = forms.ChoiceField(
        choices=[], required=False, label="Категорія"
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        label="Ціна від",
        widget=forms.NumberInput(attrs={"placeholder": "Мін. ціна"}),
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        label="Ціна до",
        widget=forms.NumberInput(attrs={"placeholder": "Макс. ціна"}),
    )
    manufacturer = forms.CharField(
        required=False,
        label="Виробник (Продавець)",
        widget=forms.TextInput(attrs={"placeholder": "Ім'я продавця"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].choices = self._get_dynamic_choices()

    @staticmethod
    def _get_dynamic_choices():
        """Динамічно генерує список категорій на основі підкласів Product."""
        choices = [("", "Всі категорії")]
        # Використовуємо інтроспекцію підкласів для справжнього OOP підходу
        for cls in Product.__subclasses__():
            choices.append((cls._meta.model_name, cls._meta.verbose_name_plural))
        choices.append(("other", "Інше"))
        return choices

