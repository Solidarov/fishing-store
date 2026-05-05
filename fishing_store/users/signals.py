from django.dispatch import receiver
from django.db.models.signals import post_save

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
