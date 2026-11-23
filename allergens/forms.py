import re

from django import forms
from django.db.models import Q

from .models import Allergen, AllergenProfile, ProfileAllergen, Severity

MAX_CUSTOM_ALLERGENS = 10  # BR-08
CUSTOM_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z \-'/]*$")


class ProfileNotesForm(forms.ModelForm):
    class Meta:
        model = AllergenProfile
        fields = ["dietary_notes", "medical_flags"]
        labels = {
            "dietary_notes": "Dietary notes",
            "medical_flags": "Medical flags",
        }
        help_texts = {
            "dietary_notes": "For example: celiac, no gluten traces. Up to 500 characters.",
            "medical_flags": "For example: carries an epinephrine auto-injector. Up to 500 characters.",
        }
        widgets = {
            "dietary_notes": forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
            "medical_flags": forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
        }

    def clean_dietary_notes(self):
        return self.cleaned_data["dietary_notes"].strip()

    def clean_medical_flags(self):
        return self.cleaned_data["medical_flags"].strip()


class ProfileAllergenForm(forms.ModelForm):
    """Add an allergen to the profile (pick a major one or type a custom one) or edit its severity."""

    custom_name = forms.CharField(
        max_length=50,
        required=False,
        label="Or type a custom allergen",
        help_text="2 to 50 letters. You can create up to 10 custom allergens.",
    )

    class Meta:
        model = ProfileAllergen
        fields = ["allergen", "severity", "notes"]
        labels = {"allergen": "Allergen", "severity": "Severity", "notes": "Note for the kitchen"}
        help_texts = {"notes": "Optional. For example: even trace amounts are unsafe."}
        widgets = {
            "notes": forms.TextInput(attrs={"maxlength": 200}),
            "severity": forms.RadioSelect,
        }

    def __init__(self, *args, profile, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["severity"].choices = Severity.choices  # no blank "-----" option in the picker
        self.profile = profile
        self.instance.profile = profile
        allergen_field = self.fields["allergen"]

        if self.instance.pk:
            # Editing: the allergen itself is fixed, only severity and note change.
            allergen_field.queryset = Allergen.objects.filter(pk=self.instance.allergen_id)
            allergen_field.disabled = True
            del self.fields["custom_name"]
        else:
            taken = profile.items.values_list("allergen_id", flat=True)
            allergen_field.queryset = (
                Allergen.objects.filter(is_active=True)
                .filter(Q(allergen_type=Allergen.Type.MAJOR) | Q(created_by=profile.user))
                .exclude(pk__in=taken)
            )
            allergen_field.required = False
            allergen_field.empty_label = "Select an allergen"

    def clean_custom_name(self):
        name = " ".join((self.cleaned_data.get("custom_name") or "").split())
        if name:
            if len(name) < 2:
                raise forms.ValidationError("Custom allergen names must be 2 to 50 characters long.")
            if not CUSTOM_NAME_PATTERN.match(name):
                raise forms.ValidationError("Use letters, spaces, hyphens or apostrophes only.")
        return name

    def clean(self):
        cleaned = super().clean()
        if self.instance.pk:
            return cleaned

        allergen = cleaned.get("allergen")
        name = cleaned.get("custom_name")
        user = self.profile.user

        if allergen and name:
            raise forms.ValidationError("Choose an allergen from the list or type a custom one, not both.")
        if not allergen and not name:
            if "custom_name" not in self.errors:
                self.add_error("allergen", "Select an allergen or type a custom one.")
            return cleaned

        if name:
            existing = (
                Allergen.objects.filter(allergen_name__iexact=name)
                .filter(Q(allergen_type=Allergen.Type.MAJOR) | Q(created_by=user))
                .first()
            )
            if existing:
                if self.profile.items.filter(allergen=existing).exists():
                    self.add_error("custom_name", f"{existing.allergen_name} is already in your profile.")
                else:
                    cleaned["allergen"] = existing  # reuse instead of making a duplicate
            elif Allergen.objects.filter(created_by=user, allergen_type=Allergen.Type.CUSTOM).count() >= MAX_CUSTOM_ALLERGENS:
                self.add_error("custom_name", f"You can create at most {MAX_CUSTOM_ALLERGENS} custom allergens.")
        elif self.profile.items.filter(allergen=allergen).exists():
            # BR-07 (the dropdown already hides these, this covers tampered requests)
            self.add_error("allergen", f"{allergen} is already in your profile.")
        return cleaned

    def save(self, commit=True):
        if not self.instance.pk:
            allergen = self.cleaned_data.get("allergen")
            if allergen is None:
                allergen = Allergen.objects.create(
                    allergen_name=self.cleaned_data["custom_name"],
                    allergen_type=Allergen.Type.CUSTOM,
                    created_by=self.profile.user,
                )
            self.instance.allergen = allergen
        return super().save(commit=commit)


class AllergenCatalogForm(forms.ModelForm):
    """Admin only: add or rename a MAJOR allergen in the shared catalog."""

    class Meta:
        model = Allergen
        fields = ["allergen_name", "is_active"]
        labels = {"allergen_name": "Allergen name", "is_active": "Available to diners"}

    def clean_allergen_name(self):
        name = " ".join(self.cleaned_data["allergen_name"].split())
        if len(name) < 2:
            raise forms.ValidationError("Allergen names must be 2 to 50 characters long.")
        clash = Allergen.objects.filter(allergen_type=Allergen.Type.MAJOR, allergen_name__iexact=name)
        if self.instance.pk:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError("That allergen is already in the catalog.")
        return name