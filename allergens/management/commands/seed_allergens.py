from django.core.management.base import BaseCommand

from allergens.models import Allergen

# SDD 4.5: major food allergens
MAJOR_ALLERGENS = [
    "Peanuts", "Tree nuts", "Milk", "Eggs", "Wheat / Gluten",
    "Soy", "Fish", "Shellfish", "Sesame",
]


class Command(BaseCommand):
    help = "Seed the major allergen catalog (safe to run more than once)."

    def handle(self, *args, **options):
        created = 0
        for name in MAJOR_ALLERGENS:
            _, was_created = Allergen.objects.get_or_create(
                allergen_name=name,
                allergen_type=Allergen.Type.MAJOR,
                defaults={"is_active": True},
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Major allergens ready ({created} new)."))