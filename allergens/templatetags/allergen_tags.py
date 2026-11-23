from django import template

from allergens.models import Allergen
from allergens.utils import get_profile, is_admin_user

register = template.Library()


@register.inclusion_tag("allergens/_dashboard_widget.html", takes_context=True)
def allergen_dashboard(context):
    """Usage in a dashboard template:  {% load allergen_tags %} {% allergen_dashboard %}"""
    request = context.get("request")
    user = getattr(request, "user", None) or context.get("user")
    data = {"show": False}
    if user is None or not user.is_authenticated:
        return data
    data["show"] = True
    if is_admin_user(user):
        data.update(
            is_admin=True,
            major_count=Allergen.objects.filter(allergen_type=Allergen.Type.MAJOR, is_active=True).count(),
        )
    else:
        profile = get_profile(user)
        items = list(profile.items.select_related("allergen"))
        data.update(is_admin=False, items=items[:4], item_count=len(items))
    return data