from django.urls import path

from . import views

app_name = "chefcards"

urlpatterns = [
    path("", views.card_list, name="list"),
    path("new/", views.card_create, name="create"),
    path("<int:pk>/", views.card_detail, name="detail"),
    path("<int:pk>/edit/", views.card_edit, name="edit"),
    path("<int:pk>/delete/", views.card_delete, name="delete"),
    path("<int:pk>/activate/", views.card_activate, name="activate"),
    path("<int:pk>/archive/", views.card_archive, name="archive"),
    path("all/", views.all_cards, name="all_cards"),
    path("rules/", views.rule_list, name="rules"),
    path("rules/add/", views.rule_add, name="rule_add"),
    path("rules/<int:pk>/edit/", views.rule_edit, name="rule_edit"),
    path("rules/<int:pk>/toggle/", views.rule_toggle, name="rule_toggle"),
]
