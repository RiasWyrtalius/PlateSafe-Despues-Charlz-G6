from django.db import models
from django.db.models import Q

from allergens.models import AllergenProfile, Severity


class PreparationRule(models.Model):
    """Library of kitchen handling / cross-contamination rules (SDD 4.4.9)."""

    class RuleType(models.TextChoices):
        CROSS_CONTAMINATION = "CROSS_CONTAMINATION", "Cross-contamination"
        HANDLING = "HANDLING", "Handling"
        INGREDIENT = "INGREDIENT", "Ingredient"

    AUTO_SEVERITY_CHOICES = [
        (Severity.SEVERE, "Severe or higher"),
        (Severity.ANAPHYLACTIC, "Anaphylactic only"),
    ]

    rule_code = models.CharField(max_length=30, unique=True)
    rule_text = models.CharField(max_length=300)
    rule_type = models.CharField(max_length=25, choices=RuleType.choices)
    auto_min_severity = models.CharField(max_length=15, choices=AUTO_SEVERITY_CHOICES, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["rule_type", "rule_code"]

    def __str__(self):
        return self.rule_text


class ChefCard(models.Model):
    """Digital Chef Safety Card built from a diner's allergen profile (SDD 4.4.11)."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    profile = models.ForeignKey(AllergenProfile, on_delete=models.CASCADE, related_name="chef_cards")
    card_title = models.CharField(max_length=100)
    version_no = models.PositiveIntegerField(default=1)
    card_status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    special_instructions = models.CharField(max_length=500, blank=True)
    rules = models.ManyToManyField(PreparationRule, through="ChefCardRule", related_name="cards")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile"],
                condition=Q(card_status="ACTIVE"),
                name="one_active_chef_card_per_profile",
            ),
        ]

    def __str__(self):
        return f"{self.card_title} (v{self.version_no})"

    @property
    def owner(self):
        return self.profile.user

    @property
    def is_active(self):
        return self.card_status == self.Status.ACTIVE


class ChefCardRule(models.Model):
    """Rules attached to a card (many-to-many link, SDD 4.4.12)."""

    card = models.ForeignKey(ChefCard, on_delete=models.CASCADE, related_name="card_rules")
    rule = models.ForeignKey(PreparationRule, on_delete=models.PROTECT, related_name="card_links")
    custom_note = models.CharField(max_length=200, blank=True)
    is_auto_added = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_auto_added", "rule__rule_type", "rule__rule_code"]
        constraints = [
            models.UniqueConstraint(fields=["card", "rule"], name="uniq_card_rule"),
        ]

    def __str__(self):
        return f"{self.card} · {self.rule.rule_code}"
