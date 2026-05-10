from decimal import Decimal

from store.models import Product


class CartService:
    """
    Сервісний шар для керування кошиком покупок, що зберігається в сесії.
    """

    CART_SESSION_ID = "cart"

    def __init__(self, request):
        """Ініціалізує сервіс кошика, отримуючи доступ до сесії."""
        self.session = request.session
        cart = self.session.get(self.CART_SESSION_ID)
        if not cart:
            cart = self.session[self.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Додає товар до кошика або оновлює його кількість.
        Виконує перевірку наявності товару та залишків на складі.
        """
        if not product.is_available:
            raise ValueError("Цей товар недоступний для покупки.")

        product_id = str(product.id)
        current_quantity = self.cart.get(product_id, {}).get("quantity", 0)

        if override_quantity:
            new_quantity = quantity
        else:
            new_quantity = current_quantity + quantity

        if product.stock < new_quantity:
            raise ValueError(f"На складі є лише {product.stock} одиниць цього товару.")

        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0, "price": str(product.price)}

        self.cart[product_id]["quantity"] = new_quantity
        self.save()

    def remove(self, product):
        """Видаляє товар з кошика."""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Ітерує по товарах у кошику, додаючи до них об'єкти Product.
        Це дозволяє отримати повну інформацію про товар у шаблонах.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(
            id__in=product_ids, is_active=True
        ).select_related("seller")

        cart = self.cart.copy()
        for product in products:
            if product.is_available:  # Додаткова перевірка
                cart[str(product.id)]["product"] = product

        for item in cart.values():
            if "product" in item:
                item["price"] = Decimal(item["price"])
                item["total_price"] = item["price"] * item["quantity"]
                yield item

    def __len__(self):
        """Повертає загальну кількість товарів у кошику."""
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        """Обчислює загальну вартість всіх товарів у кошику."""
        return sum(
            Decimal(item["price"]) * item["quantity"] for item in self.cart.values()
        )

    def clear(self):
        """Повністю очищує кошик."""
        if self.CART_SESSION_ID in self.session:
            del self.session[self.CART_SESSION_ID]
            self.save()

    def save(self):
        """Зберігає зміни в сесії."""
        self.session.modified = True
