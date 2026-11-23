from django.contrib import admin

from .models import Allergen, AllergenProfile, ProfileAllergen


@admin.register(Allergen)
class AllergenAdmin(admin.ModelAdmin):
    list_display = ("allergen_name", "allergen_type", "created_by", "is_active")
    list_filter = ("allergen_type", "is_active")
    search_fields = ("allergen_name",)


class ProfileAllergenInline(admin.TabularInline):
    model = ProfileAllergen
    extra = 0


@admin.register(AllergenProfile)
class AllergenProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "updated_at")
    inlines = [ProfileAllergenInline]