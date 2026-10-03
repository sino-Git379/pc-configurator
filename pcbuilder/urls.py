from django.urls import path

from . import views


urlpatterns = [
    path("", views.component_catalog, name="component_catalog"),
    path("components/new/", views.component_create, name="component_create"),
    path("components/<int:component_id>/add/", views.add_component_to_build, name="add_component_to_build"),
    path("cart/components/<int:component_id>/remove/", views.remove_component_from_build, name="remove_component_from_build"),
    path("builds/<int:build_id>/select/", views.select_build, name="select_build"),
    path("builds/save/", views.save_build, name="save_build"),
    path("auth/login/", views.auth_login, name="auth_login"),
    path("auth/register/", views.auth_register, name="auth_register"),
    path("auth/logout/", views.auth_logout, name="auth_logout"),
    path("checkout/", views.checkout, name="checkout"),
]