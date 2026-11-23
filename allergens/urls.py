from django.urls import path

from . import views

app_name = "allergens"

urlpatterns = [
    path("", views.profile_detail, name="profile"),
    path("notes/", views.profile_notes_edit, name="notes_edit"),
    path("add/", views.allergen_add, name="add"),
    path("<int:pk>/edit/", views.allergen_edit, name="edit"),
    path("<int:pk>/delete/", views.allergen_delete, name="delete"),
    # admin role
    path("catalog/", views.catalog_list, name="catalog"),
    path("catalog/add/", views.catalog_add, name="catalog_add"),
    path("catalog/<int:pk>/edit/", views.catalog_edit, name="catalog_edit"),
    path("catalog/<int:pk>/toggle/", views.catalog_toggle, name="catalog_toggle"),
]