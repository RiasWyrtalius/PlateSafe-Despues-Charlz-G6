from django import template
from django.utils import timezone

from allergens.utils import get_profile, is_admin_user
from chefcards.models import ChefCard, PreparationRule

register = template.Library()


@register.simple_tag
def time_greeting():
    hour = timezone.localtime().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


@register.simple_tag(takes_context=True)
def has_active_card(context):
    request = context.get("request")
    user = getattr(request, "user", None) or context.get("user")
    if user is None or not user.is_authenticated:
        return False
    return get_profile(user).chef_cards.filter(card_status=ChefCard.Status.ACTIVE).exists()


@register.inclusion_tag("chefcards/_dashboard_widget.html", takes_context=True)
def chefcard_dashboard(context):
    request = context.get("request")
    user = getattr(request, "user", None) or context.get("user")
    data = {"show": False}
    if user is None or not user.is_authenticated:
        return data
    data["show"] = True
    if is_admin_user(user):
        data.update(
            is_admin=True,
            card_count=ChefCard.objects.count(),
            active_count=ChefCard.objects.filter(card_status=ChefCard.Status.ACTIVE).count(),
            rule_count=PreparationRule.objects.filter(is_active=True).count(),
        )
        return data
    profile = get_profile(user)
    active_card = profile.chef_cards.filter(card_status=ChefCard.Status.ACTIVE).first()
    data.update(
        is_admin=False,
        card_count=profile.chef_cards.count(),
        active_card=active_card,
        has_allergens=profile.items.exists(),
    )
    if active_card:
        data["items"] = sorted(
            profile.items.select_related("allergen"),
            key=lambda item: (-item.severity_rank, item.allergen.allergen_name),
        )
        data["rule_count"] = active_card.card_rules.count()
    return data
