from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in

from users.models import CustomUser, CustomerProfile, SellerProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Автоматичне створення або перевірка наявності профілю при кожному збереженні.
    """
    if instance.role == CustomUser.Role.CUSTOMER:
        CustomerProfile.objects.get_or_create(user=instance)
    elif instance.role == CustomUser.Role.SELLER:
        SellerProfile.objects.get_or_create(user=instance)


@receiver(user_logged_in)
def merge_cart_on_login(sender, user, request, **kwargs):
    """
    Злиття кошика при вході користувача.
    Оскільки при логіні сесія може оновлюватися, ми фіксуємо вміст кошика
    та переконуємося, що він доступний у новій сесії.
    """
    cart = request.session.get("cart")
    if cart:
        # Django автоматично оновлює ID сесії при login(),
        # але ми явно переконуємося, що кошик збережено.
        request.session["cart"] = cart
        request.session.modified = True
