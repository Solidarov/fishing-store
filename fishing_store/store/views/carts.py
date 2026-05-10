from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages

from store.services import CartService
from store.models import Product


@require_POST
def cart_add(request, product_id):
    """Додавання товару в кошик."""
    cart = CartService(request)
    product = get_object_or_404(Product, id=product_id)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1

    try:
        cart.add(product=product, quantity=quantity, override_quantity=False)
        messages.success(request, f'"{product.name}" додано до кошика.')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect("store:product_detail", pk=product_id)


def cart_remove(request, product_id):
    """Видалення товару з кошика."""
    cart = CartService(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f'"{product.name}" видалено з кошика.')
    return redirect("store:cart_detail")


def cart_clear(request):
    """Повне очищення кошика."""
    cart = CartService(request)
    cart.clear()
    messages.info(request, "Ваш кошик було очищено.")
    return redirect("store:cart_detail")


def cart_detail(request):
    """Відображення сторінки кошика."""
    return render(request, "store/cart_detail.html")
