from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/diner/", views.diner_dashboard, name="diner_dashboard"),
    path("dashboard/kitchen/", views.kitchen_dashboard, name="kitchen_dashboard"),
]