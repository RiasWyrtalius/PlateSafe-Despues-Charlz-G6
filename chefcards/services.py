"""Business rules for the Chef Card Builder (SDD BR-13 to BR-16)."""
from django.db import transaction

from allergens.models import SEVERITY_RANK

from .models import ChefCard, ChefCardRule, PreparationRule


def highest_severity_rank(profile):
    return max((SEVERITY_RANK[item.severity] for item in profile.items.all()), default=0)


def required_auto_rules(profile):
    """BR-14: every active rule whose auto_min_severity is met by an allergen in the profile."""
    top = highest_severity_rank(profile)
    rules = PreparationRule.objects.filter(is_active=True, auto_min_severity__isnull=False)
    return [rule for rule in rules if top >= SEVERITY_RANK[rule.auto_min_severity]]


def auto_rules_with_reasons(profile):
    """Same as required_auto_rules, plus which allergens triggered each rule (for the UI)."""
    items = list(profile.items.select_related("allergen"))
    result = []
    for rule in required_auto_rules(profile):
        threshold = SEVERITY_RANK[rule.auto_min_severity]
        names = [i.allergen.allergen_name for i in items if SEVERITY_RANK[i.severity] >= threshold]
        result.append({"rule": rule, "reasons": names})
    return result


def sync_auto_rules(card):
    """Add missing automatic rules and drop automatic rules that no longer apply."""
    needed = {rule.pk: rule for rule in required_auto_rules(card.profile)}
    existing = {link.rule_id: link for link in card.card_rules.all()}
    changed = False
    for rule_id, rule in needed.items():
        link = existing.get(rule_id)
        if link is None:
            ChefCardRule.objects.create(card=card, rule=rule, is_auto_added=True)
            changed = True
        elif not link.is_auto_added:
            link.is_auto_added = True
            link.save(update_fields=["is_auto_added"])
    for rule_id, link in existing.items():
        if link.is_auto_added and rule_id not in needed:
            link.delete()
            changed = True
    return changed


def mark_card_changed(card):
    """BR-16: a change to an ACTIVE card bumps its version and sends it back to DRAFT."""
    if card.card_status == ChefCard.Status.ACTIVE:
        card.version_no += 1
        card.card_status = ChefCard.Status.DRAFT
        card.save(update_fields=["version_no", "card_status", "updated_at"])
        return True
    return False


def refresh_cards_for_profile(profile):
    """Called when the diner adds, edits or removes an allergen."""
    for card in profile.chef_cards.exclude(card_status=ChefCard.Status.ARCHIVED):
        sync_auto_rules(card)
        mark_card_changed(card)


@transaction.atomic
def activate_card(card):
    """BR-15: only one ACTIVE card; the previous active card is archived."""
    (card.profile.chef_cards
        .filter(card_status=ChefCard.Status.ACTIVE)
        .exclude(pk=card.pk)
        .update(card_status=ChefCard.Status.ARCHIVED))
    sync_auto_rules(card)
    card.card_status = ChefCard.Status.ACTIVE
    card.save(update_fields=["card_status", "updated_at"])
