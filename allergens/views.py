from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AllergenCatalogForm, ProfileAllergenForm, ProfileNotesForm
from .models import Allergen, ProfileAllergen
from .utils import admin_required, get_profile, is_admin_user


# ---------- Diner: allergen profile ----------

@login_required
def profile_detail(request):
    """READ: the logged-in diner's allergen profile."""
    profile = get_profile(request.user)
    items = profile.items.select_related("allergen")
    return render(request, "allergens/profile.html", {
        "profile": profile,
        "items": items,
        "is_admin": is_admin_user(request.user),
    })


@login_required
def profile_notes_edit(request):
    """UPDATE: dietary notes and medical flags (BR-09)."""
    profile = get_profile(request.user)
    form = ProfileNotesForm(request.POST or None, instance=profile)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Your dietary notes were saved.")
            return redirect("allergens:profile")
        messages.error(request, "Please fix the errors below.")
    return render(request, "allergens/notes_form.html", {"form": form})


@login_required
def allergen_add(request):
    """CREATE: add an allergen (major or custom) with a severity (BR-06, BR-07, BR-08)."""
    profile = get_profile(request.user)
    form = ProfileAllergenForm(request.POST or None, profile=profile)
    if request.method == "POST":
        if form.is_valid():
            item = form.save()
            messages.success(request, f"{item.allergen} was added as {item.get_severity_display()}.")
            return redirect("allergens:profile")
        messages.error(request, "The allergen was not added. Please fix the errors below.")
    return render(request, "allergens/allergen_form.html", {"form": form, "is_edit": False})


@login_required
def allergen_edit(request, pk):
    """UPDATE: change severity or note. Users can only edit their own entries."""
    profile = get_profile(request.user)
    item = get_object_or_404(ProfileAllergen, pk=pk, profile=profile)
    form = ProfileAllergenForm(request.POST or None, instance=item, profile=profile)
    if request.method == "POST":
        if form.is_valid():
            item = form.save()
            messages.success(request, f"{item.allergen} was updated.")
            return redirect("allergens:profile")
        messages.error(request, "Please fix the errors below.")
    return render(request, "allergens/allergen_form.html", {"form": form, "is_edit": True, "item": item})


@login_required
def allergen_delete(request, pk):
    """DELETE: remove an allergen from the profile after confirmation."""
    profile = get_profile(request.user)
    item = get_object_or_404(ProfileAllergen.objects.select_related("allergen"), pk=pk, profile=profile)
    if request.method == "POST":
        name = str(item.allergen)
        item.delete()
        messages.success(request, f"{name} was removed from your profile.")
        return redirect("allergens:profile")
    return render(request, "allergens/allergen_confirm_delete.html", {"item": item})


# ---------- Admin: shared allergen catalog ----------

@admin_required
def catalog_list(request):
    allergens = Allergen.objects.filter(allergen_type=Allergen.Type.MAJOR)
    custom_count = Allergen.objects.filter(allergen_type=Allergen.Type.CUSTOM).count()
    return render(request, "allergens/catalog_list.html", {"allergens": allergens, "custom_count": custom_count})


@admin_required
def catalog_add(request):
    form = AllergenCatalogForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            allergen = form.save(commit=False)
            allergen.allergen_type = Allergen.Type.MAJOR
            allergen.created_by = None
            allergen.save()
            messages.success(request, f"{allergen} was added to the catalog.")
            return redirect("allergens:catalog")
        messages.error(request, "Please fix the errors below.")
    return render(request, "allergens/catalog_form.html", {"form": form, "is_edit": False})


@admin_required
def catalog_edit(request, pk):
    allergen = get_object_or_404(Allergen, pk=pk, allergen_type=Allergen.Type.MAJOR)
    form = AllergenCatalogForm(request.POST or None, instance=allergen)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f"{allergen} was updated.")
            return redirect("allergens:catalog")
        messages.error(request, "Please fix the errors below.")
    return render(request, "allergens/catalog_form.html", {"form": form, "is_edit": True})


@admin_required
@require_POST
def catalog_toggle(request, pk):
    """Soft delete: inactive allergens can't be newly selected but stay on existing profiles."""
    allergen = get_object_or_404(Allergen, pk=pk, allergen_type=Allergen.Type.MAJOR)
    allergen.is_active = not allergen.is_active
    allergen.save(update_fields=["is_active"])
    state = "available to diners again" if allergen.is_active else "hidden from new selections"
    messages.success(request, f"{allergen} is now {state}.")
    return redirect("allergens:catalog")