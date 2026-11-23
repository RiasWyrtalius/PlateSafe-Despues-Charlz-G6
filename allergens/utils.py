from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import AllergenProfile

# Role values that count as the back-office/admin role.
ADMIN_ROLE_VALUES = {"ADMIN", "STAFF", "KITCHEN"}


def is_admin_user(user):
    """True if the user has the admin role (is_staff, is_superuser, or role = ADMIN/STAFF)."""
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser or user.is_staff:
        return True
    role = getattr(user, "role", None)
    if role is None:
        role = getattr(getattr(user, "profile", None), "role", None)
    return str(role or "").upper() in ADMIN_ROLE_VALUES


def admin_required(view_func):
    """Only logged-in admins can open the view; everyone else is sent back with a message."""

    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_admin_user(request.user):
            messages.error(request, "You do not have permission to open that page.")
            return redirect("allergens:profile")
        return view_func(request, *args, **kwargs)

    return wrapper


def get_profile(user):
    """Return the user's allergen profile, creating it if PD1 accounts don't have one yet (BR-05)."""
    profile, _ = AllergenProfile.objects.get_or_create(user=user)
    return profile