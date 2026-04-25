from django.dispatch import receiver
from django.db.models.signals import post_save

from users.models import CustomUser, CustomerProfile, SellerProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Автоматичне створення профілів для продавця та користувача
    """
    if created:
        if instance.role == CustomUser.Role.CUSTOMER:
            CustomerProfile.objects.create(user=instance)
        elif instance.role == CustomUser.Role.SELLER:
            SellerProfile.objects.create(user=instance)
