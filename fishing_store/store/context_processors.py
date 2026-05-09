from .services import CartService

def cart(request):
    """
    Контекстний процесор для надання доступу до кошика у всіх шаблонах.
    """
    return {'cart': CartService(request)}
