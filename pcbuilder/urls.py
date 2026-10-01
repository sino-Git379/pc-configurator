from django.urls import path

from . import views


urlpatterns = [
	path("", views.component_catalog, name="component_catalog"),
	path("components/new/", views.component_create, name="component_create"),
	path(
		"components/<int:component_id>/add/",
		views.add_component_to_build,
		name="add_component_to_build",
	),
]