from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ComponentForm
from .models import Build, BuildItem, Category, Component


def component_catalog(request):
    categories = Category.objects.all()
    selected_slug = request.GET.get("category", "")
    selected_category = categories.filter(slug=selected_slug).first() if selected_slug else None
    components = Component.objects.select_related("category")
    if selected_slug:
        components = components.filter(category__slug=selected_slug)

    component_data = [
        {
            "id": component.pk,
            "name": component.name,
            "category": component.category.name,
            "price": str(component.price),
            "thumbnail": component.thumbnail.url if component.thumbnail else "",
            "specs": component.specs,
        }
        for component in components
    ]

    active_build = None
    active_build_id = request.session.get("active_build_id")
    if active_build_id:
        active_build = Build.objects.filter(pk=active_build_id).first()
    build_items = list(active_build.items.select_related("component") if active_build else [])

    return render(
        request,
        "pcbuilder/catalog.html",
        {
            "categories": categories,
            "selected_slug": selected_slug,
            "selected_category": selected_category,
            "components": components,
            "component_data": component_data,
            "build_items": build_items,
            "build_total": sum((item.component.price * item.quantity for item in build_items), 0),
        },
    )


@require_POST
def add_component_to_build(request, component_id):
    component = get_object_or_404(Component, pk=component_id)
    build_id = request.session.get("active_build_id")
    build = Build.objects.filter(pk=build_id).first() if build_id else None
    if build is None:
        build = Build.objects.create(title="Моя сборка")
        request.session["active_build_id"] = build.pk

    item, created = BuildItem.objects.get_or_create(build=build, component=component)
    if not created:
        item.quantity += 1
        item.save(update_fields=["quantity"])

    item_count = build.items.count()
    total_price = sum(
        (build_item.component.price * build_item.quantity for build_item in build.items.select_related("component")),
        0,
    )
    return JsonResponse(
        {
            "added": True,
            "item_count": item_count,
            "total_price": str(total_price),
            "component_name": component.name,
        }
    )


def component_create(request):
    if request.method == "POST":
        form = ComponentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("component_create")
    else:
        form = ComponentForm()

    return render(
        request,
        "pcbuilder/component_form.html",
        {"form": form, "categories": Category.objects.all()},
    )