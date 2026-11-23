from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AllergenProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_allergen_profile(sender, instance, created, **kwargs):
    """BR-05: every new account gets exactly one blank allergen profile."""
    if created:
        AllergenProfile.objects.get_or_create(user=instance)