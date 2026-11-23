import re

from django import forms

from .models import ChefCard, PreparationRule

RULE_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,29}$")


class ChefCardForm(forms.ModelForm):
    selected_rules = forms.ModelMultipleChoiceField(
        queryset=PreparationRule.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "ps-switch"}),
        label="Kitchen handling rules",
        help_text="Pick any extra rules the kitchen should follow.",
    )

    class Meta:
        model = ChefCard
        fields = ["card_title", "special_instructions"]
        labels = {"card_title": "Card title", "special_instructions": "Special instructions for the chef"}
        help_texts = {
            "card_title": "For example: Dinner card - peanut and shellfish.",
            "special_instructions": "Optional. Up to 500 characters.",
        }
        widgets = {
            "card_title": forms.TextInput(attrs={"maxlength": 100}),
            "special_instructions": forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
        }

    def __init__(self, *args, auto_rule_ids=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["selected_rules"].queryset = (
            PreparationRule.objects.filter(is_active=True).exclude(pk__in=list(auto_rule_ids))
        )
        if self.instance.pk and not self.is_bound:
            self.initial["selected_rules"] = list(
                self.instance.card_rules.filter(is_auto_added=False).values_list("rule_id", flat=True)
            )

    def clean_card_title(self):
        title = " ".join(self.cleaned_data["card_title"].split())
        if len(title) < 3:
            raise forms.ValidationError("The card title must be at least 3 characters long.")
        return title

    def clean_special_instructions(self):
        return self.cleaned_data["special_instructions"].strip()


class PreparationRuleForm(forms.ModelForm):
    """Kitchen role only: manage the shared rule library."""

    class Meta:
        model = PreparationRule
        fields = ["rule_code", "rule_text", "rule_type", "auto_min_severity", "is_active"]
        labels = {
            "rule_code": "Rule code",
            "rule_text": "Instruction shown to the kitchen",
            "rule_type": "Rule type",
            "auto_min_severity": "Add automatically when",
            "is_active": "Available on new cards",
        }
        help_texts = {"rule_code": "Capital letters, digits and underscores, e.g. SEPARATE_FRYER."}
        widgets = {"rule_text": forms.Textarea(attrs={"rows": 3, "maxlength": 300})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["auto_min_severity"].choices = [("", "Never (diner picks it)")] + list(
            PreparationRule.AUTO_SEVERITY_CHOICES
        )

    def clean_rule_code(self):
        code = self.cleaned_data["rule_code"].strip().upper()
        if not RULE_CODE_PATTERN.match(code):
            raise forms.ValidationError("Use 3 to 30 capital letters, digits or underscores, starting with a letter.")
        return code

    def clean_rule_text(self):
        text = " ".join(self.cleaned_data["rule_text"].split())
        if len(text) < 10:
            raise forms.ValidationError("Write the instruction in at least 10 characters.")
        return text

    def clean_auto_min_severity(self):
        return self.cleaned_data.get("auto_min_severity") or None
