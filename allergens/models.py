from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models


class Severity(models.TextChoices):
    MILD = "MILD", "Mild"
    MODERATE = "MODERATE", "Moderate"
    SEVERE = "SEVERE", "Severe"
    ANAPHYLACTIC = "ANAPHYLACTIC", "Anaphylactic"


SEVERITY_RANK = {
    Severity.MILD: 1,
    Severity.MODERATE: 2,
    Severity.SEVERE: 3,
    Severity.ANAPHYLACTIC: 4,
}


class Allergen(models.Model):
    """Catalog of major allergens plus diner-defined custom allergens (SDD 4.4.4)."""

    class Type(models.TextChoices):
        MAJOR = "MAJOR", "Major"
        CUSTOM = "CUSTOM", "Custom"

    allergen_name = models.CharField(max_length=50, validators=[MinLengthValidator(2)])
    allergen_type = models.CharField(max_length=10, choices=Type.choices, default=Type.MAJOR)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="custom_allergens",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["allergen_type", "allergen_name"]

    def __str__(self):
        return self.allergen_name


class AllergenProfile(models.Model):
    """One allergen profile per user (BR-05, SDD 4.4.3)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="allergen_profile",
    )
    dietary_notes = models.CharField(max_length=500, blank=True)
    medical_flags = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Allergen profile of {self.user}"


class ProfileAllergen(models.Model):
    """Allergen listed in a profile with its severity (SDD 4.4.5)."""

    profile = models.ForeignKey(AllergenProfile, on_delete=models.CASCADE, related_name="items")
    allergen = models.ForeignKey(Allergen, on_delete=models.CASCADE, related_name="profile_entries")
    severity = models.CharField(max_length=15, choices=Severity.choices)
    notes = models.CharField(max_length=200, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["allergen__allergen_name"]
        constraints = [
            models.UniqueConstraint(fields=["profile", "allergen"], name="uniq_profile_allergen"),
        ]

    def __str__(self):
        return f"{self.allergen} ({self.get_severity_display()})"

    @property
    def severity_rank(self):
        return SEVERITY_RANK[self.severity]
