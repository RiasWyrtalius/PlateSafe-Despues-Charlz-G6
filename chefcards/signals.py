from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from allergens.models import ProfileAllergen

from .services import refresh_cards_for_profile


@receiver(pre_save, sender=ProfileAllergen)
def remember_old_severity(sender, instance, **kwargs):
    instance._old_severity = None
    if instance.pk:
        instance._old_severity = (
            ProfileAllergen.objects.filter(pk=instance.pk).values_list("severity", flat=True).first()
        )


@receiver(post_save, sender=ProfileAllergen)
def allergen_saved(sender, instance, created, **kwargs):
    if created or instance.severity != getattr(instance, "_old_severity", None):
        refresh_cards_for_profile(instance.profile)


@receiver(post_delete, sender=ProfileAllergen)
def allergen_deleted(sender, instance, **kwargs):
    origin = kwargs.get("origin")
    if origin is not None and not isinstance(origin, ProfileAllergen):
        return
    refresh_cards_for_profile(instance.profile)
