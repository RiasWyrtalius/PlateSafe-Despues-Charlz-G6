from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from allergens.utils import admin_required, get_profile, is_admin_user

from .forms import ChefCardForm, PreparationRuleForm
from .models import ChefCard, ChefCardRule, PreparationRule
from .services import activate_card, auto_rules_with_reasons, mark_card_changed, sync_auto_rules


def _own_card(request, pk):
    """Diners can only touch their own cards."""
    return get_object_or_404(
        ChefCard.objects.select_related("profile__user"), pk=pk, profile__user=request.user
    )


def _save_manual_rules(card, rule_ids):
    """Replace the diner-picked rules; automatic rules are left alone (BR-14)."""
    card.card_rules.filter(is_auto_added=False).exclude(rule_id__in=rule_ids).delete()
    existing = set(card.card_rules.values_list("rule_id", flat=True))
    for rule_id in rule_ids:
        if rule_id not in existing:
            ChefCardRule.objects.create(card=card, rule_id=rule_id, is_auto_added=False)


@login_required
def card_list(request):
    """READ: the logged-in diner's cards."""
    profile = get_profile(request.user)
    cards = profile.chef_cards.prefetch_related("card_rules")
    return render(request, "chefcards/card_list.html", {
        "cards": cards,
        "allergen_count": profile.items.count(),
        "is_admin": is_admin_user(request.user),
    })


@login_required
def card_create(request):
    """CREATE: build a card from the profile (BR-13, BR-14)."""
    profile = get_profile(request.user)
    if not profile.items.exists():
        messages.error(request, "Add at least one allergen to your profile before creating a Chef Card.")
        return redirect("allergens:add")

    auto_rules = auto_rules_with_reasons(profile)
    form = ChefCardForm(request.POST or None, auto_rule_ids=[a["rule"].pk for a in auto_rules])
    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                card = form.save(commit=False)
                card.profile = profile
                card.save()
                _save_manual_rules(card, [r.pk for r in form.cleaned_data["selected_rules"]])
                sync_auto_rules(card)
            messages.success(request, f"'{card.card_title}' was created as a draft. Activate it when you're ready to show it.")
            return redirect("chefcards:detail", pk=card.pk)
        messages.error(request, "The card was not created. Please fix the errors below.")

    return render(request, "chefcards/card_form.html", {
        "form": form,
        "auto_rules": auto_rules,
        "items": profile.items.select_related("allergen"),
        "is_edit": False,
    })


@login_required
def card_detail(request, pk):
    """READ: Chef Card preview. Owners can manage it; kitchen staff can view any card read-only."""
    qs = ChefCard.objects.select_related("profile__user")
    if is_admin_user(request.user):
        card = get_object_or_404(qs, pk=pk)
    else:
        card = get_object_or_404(qs, pk=pk, profile__user=request.user)

    profile = card.profile
    items = sorted(
        profile.items.select_related("allergen"),
        key=lambda item: (-item.severity_rank, item.allergen.allergen_name),
    )
    return render(request, "chefcards/card_detail.html", {
        "card": card,
        "profile": profile,
        "items": items,
        "card_rules": card.card_rules.select_related("rule"),
        "is_owner": profile.user_id == request.user.id,
    })


@login_required
def card_edit(request, pk):
    """UPDATE: title, instructions and picked rules (BR-16 on active cards)."""
    card = _own_card(request, pk)
    if card.card_status == ChefCard.Status.ARCHIVED:
        messages.error(request, "Archived cards can't be edited. Create a new card instead.")
        return redirect("chefcards:detail", pk=card.pk)

    auto_rules = auto_rules_with_reasons(card.profile)
    form = ChefCardForm(request.POST or None, instance=card, auto_rule_ids=[a["rule"].pk for a in auto_rules])
    if request.method == "POST":
        if form.is_valid():
            old_rules = set(card.card_rules.filter(is_auto_added=False).values_list("rule_id", flat=True))
            new_rules = {r.pk for r in form.cleaned_data["selected_rules"]}
            with transaction.atomic():
                card = form.save()
                _save_manual_rules(card, new_rules)
                rules_changed = sync_auto_rules(card) or old_rules != new_rules
                went_to_draft = rules_changed and mark_card_changed(card)
            if went_to_draft:
                messages.warning(request, f"Rules changed, so the card is now version {card.version_no} and back in draft. Activate it again before showing it.")
            else:
                messages.success(request, "Your Chef Card was saved.")
            return redirect("chefcards:detail", pk=card.pk)
        messages.error(request, "Please fix the errors below.")

    return render(request, "chefcards/card_form.html", {
        "form": form,
        "card": card,
        "auto_rules": auto_rules,
        "items": card.profile.items.select_related("allergen"),
        "is_edit": True,
    })


@login_required
def card_delete(request, pk):
    """DELETE: remove a card after confirmation."""
    card = _own_card(request, pk)
    if request.method == "POST":
        title = card.card_title
        card.delete()
        messages.success(request, f"'{title}' was deleted.")
        return redirect("chefcards:list")
    return render(request, "chefcards/card_confirm_delete.html", {"card": card})


@login_required
@require_POST
def card_activate(request, pk):
    """BR-13 + BR-15: make this the one card shown to the kitchen."""
    card = _own_card(request, pk)
    if not card.profile.items.exists():
        messages.error(request, "Add at least one allergen before activating a Chef Card.")
        return redirect("chefcards:detail", pk=card.pk)
    activate_card(card)
    messages.success(request, f"'{card.card_title}' is now your active Chef Card. Any previously active card was archived.")
    return redirect("chefcards:detail", pk=card.pk)


@login_required
@require_POST
def card_archive(request, pk):
    card = _own_card(request, pk)
    card.card_status = ChefCard.Status.ARCHIVED
    card.save(update_fields=["card_status", "updated_at"])
    messages.success(request, f"'{card.card_title}' was archived.")
    return redirect("chefcards:list")


@admin_required
def all_cards(request):
    status = request.GET.get("status", "")
    cards = ChefCard.objects.select_related("profile__user").prefetch_related("card_rules")
    if status in ChefCard.Status.values:
        cards = cards.filter(card_status=status)
    return render(request, "chefcards/admin_cards.html", {
        "cards": cards,
        "status": status,
        "statuses": ChefCard.Status.choices,
    })


@admin_required
def rule_list(request):
    rules = PreparationRule.objects.all()
    return render(request, "chefcards/rule_list.html", {"rules": rules})


@admin_required
def rule_add(request):
    form = PreparationRuleForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            rule = form.save()
            messages.success(request, f"Rule {rule.rule_code} was added.")
            return redirect("chefcards:rules")
        messages.error(request, "Please fix the errors below.")
    return render(request, "chefcards/rule_form.html", {"form": form, "is_edit": False})


@admin_required
def rule_edit(request, pk):
    rule = get_object_or_404(PreparationRule, pk=pk)
    form = PreparationRuleForm(request.POST or None, instance=rule)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f"Rule {rule.rule_code} was updated.")
            return redirect("chefcards:rules")
        messages.error(request, "Please fix the errors below.")
    return render(request, "chefcards/rule_form.html", {"form": form, "is_edit": True, "rule": rule})


@admin_required
@require_POST
def rule_toggle(request, pk):
    """Soft delete: rules used on cards are deactivated instead of deleted."""
    rule = get_object_or_404(PreparationRule, pk=pk)
    rule.is_active = not rule.is_active
    rule.save(update_fields=["is_active"])
    state = "active" if rule.is_active else "inactive"
    messages.success(request, f"Rule {rule.rule_code} is now {state}.")
    return redirect("chefcards:rules")