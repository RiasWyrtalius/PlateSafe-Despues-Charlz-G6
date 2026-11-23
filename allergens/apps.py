from django.apps import AppConfig


class AllergensConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "allergens"
    verbose_name = "Allergen Profiles"

    def ready(self):
        from . import signals  # noqa: F401