from django.core.management.base import BaseCommand

from chefcards.models import PreparationRule

RULES = [
    ("CLEAN_UTENSILS", "Use clean utensils and a clean cutting board.", "HANDLING", "SEVERE"),
    ("CHANGE_GLOVES", "Change gloves and wash hands before handling my food.", "HANDLING", "SEVERE"),
    ("SEPARATE_FRYER", "Use a separate, cleaned fryer or pan.", "CROSS_CONTAMINATION", "ANAPHYLACTIC"),
    ("KEEP_SEPARATE", "Prepare, plate and carry this dish separately from other orders.", "CROSS_CONTAMINATION", "ANAPHYLACTIC"),
    ("NO_SHARED_GARNISH", "Keep my plate away from shared garnish stations.", "CROSS_CONTAMINATION", None),
    ("NO_SHARED_SAUCES", "Don't use shared sauces or dressings.", "INGREDIENT", None),
    ("SAUCES_ON_SIDE", "Serve sauces on the side.", "INGREDIENT", None),
]


class Command(BaseCommand):
    help = "Seed the preparation rule library (safe to run more than once)."

    def handle(self, *args, **options):
        for code, text, rule_type, auto in RULES:
            PreparationRule.objects.update_or_create(
                rule_code=code,
                defaults={"rule_text": text, "rule_type": rule_type, "auto_min_severity": auto, "is_active": True},
            )
        self.stdout.write(self.style.SUCCESS(f"{len(RULES)} preparation rules ready."))
