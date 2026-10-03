from decimal import Decimal

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import IntegerField, Sum, Value
from django.db.models.functions import Coalesce
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .forms import CheckoutForm, ComponentForm
from .models import Build, BuildItem, Category, Component, UserOrder, UserOrderItem
from .services.checker import check_compatibility


def component_catalog(request):
    categories = Category.objects.all()
    selected_slug = request.GET.get("category", "")
    selected_category = categories.filter(slug=selected_slug).first() if selected_slug else None
    selected_sort = request.GET.get("sort", "popular")
    filter_active_build = request.GET.get("build") == "active"
    active_build = _get_active_build(request)
    components = Component.objects.select_related("category")
    if selected_slug:
        components = components.filter(category__slug=selected_slug)
    if filter_active_build:
        if active_build:
            components = components.filter(pk__in=active_build.items.values("component_id"))
        else:
            components = components.none()

    if selected_sort == "price_asc":
        components = components.order_by("price", "name")
    elif selected_sort == "price_desc":
        components = components.order_by("-price", "name")
    else:
        selected_sort = "popular"
        components = components.annotate(
            popularity=Coalesce(Sum("build_items__quantity"), Value(0), output_field=IntegerField())
        ).order_by("-popularity", "name")

    active_component_ids = set(
        active_build.items.values_list("component_id", flat=True)
    ) if active_build else set()

    component_data = [
        {
            "id": component.pk,
            "name": component.name,
            "category": component.category.name,
            "price": str(component.price),
            "thumbnail": (
                component.thumbnail.url
                if component.thumbnail
                else component.thumbnail_url
            ),
            "thumbnail_source_url": component.thumbnail_source_url,
            "thumbnail_credit": component.thumbnail_credit,
            "specs": component.specs,
            "is_in_build": component.pk in active_component_ids,
        }
        for component in components
    ]

    return render(
        request,
        "pcbuilder/catalog.html",
        {
            "categories": categories,
            "selected_slug": selected_slug,
            "selected_category": selected_category,
            "selected_sort": selected_sort,
            "filter_active_build": filter_active_build,
            "active_build": active_build,
            "components": components,
            "component_data": component_data,
        },
    )


@require_POST
def add_component_to_build(request, component_id):
    component = get_object_or_404(Component, pk=component_id)
    build_id = request.session.get("active_build_id")
    build = Build.objects.filter(pk=build_id).first() if build_id else None
    if build is None:
        build = Build.objects.create(
            title="Моя сборка",
            user=request.user if request.user.is_authenticated else None,
        )
        request.session["active_build_id"] = build.pk
    elif request.user.is_authenticated and build.user_id is None:
        build.user = request.user
        build.save(update_fields=["user"])
    elif request.user.is_authenticated and build.user_id != request.user.pk:
        build_items = list(build.items.all())
        build = Build.objects.create(user=request.user, title=build.title)
        BuildItem.objects.bulk_create(
            [
                BuildItem(build=build, component_id=item.component_id, quantity=item.quantity)
                for item in build_items
            ]
        )
        request.session["active_build_id"] = build.pk

    item, created = BuildItem.objects.get_or_create(build=build, component=component)
    if not created:
        item.quantity += 1
        item.save(update_fields=["quantity"])

    return JsonResponse({"added": True, "component_name": component.name, **_cart_payload(build)})


@require_POST
def remove_component_from_build(request, component_id):
    build_id = request.session.get("active_build_id")
    build = Build.objects.filter(pk=build_id).first() if build_id else None
    if build is None:
        return JsonResponse({"error": "Сборка не найдена."}, status=404)
    if request.user.is_authenticated and build.user_id not in (None, request.user.pk):
        return JsonResponse({"error": "Нет доступа к этой сборке."}, status=403)

    BuildItem.objects.filter(build=build, component_id=component_id).delete()
    return JsonResponse(_cart_payload(build))


@require_POST
def select_build(request, build_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Войдите, чтобы выбрать сборку."}, status=401)
    build = get_object_or_404(Build, pk=build_id, user=request.user, status=Build.Status.DRAFT)
    request.session["active_build_id"] = build.pk
    return JsonResponse({"success": True, "build_id": build.pk, "build_title": build.title})


@require_POST
def save_build(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "errors": ["Войдите, чтобы сохранить сборку."]}, status=401)

    build = _get_active_build(request)
    if build is None or not build.items.exists():
        return JsonResponse({"success": False, "errors": ["Сборка пуста."]}, status=400)
    if build.user_id is None:
        build.user = request.user
    elif build.user_id != request.user.pk:
        return JsonResponse({"success": False, "errors": ["Нет доступа к этой сборке."]}, status=403)

    build.status = Build.Status.DRAFT
    build.save(update_fields=["user", "status"])
    return JsonResponse({"success": True, "build_id": build.pk, "title": build.title})


def _cart_payload(build):
    items = list(build.items.select_related("component", "component__category")) if build else []
    total_price = sum((item.component.price * item.quantity for item in items), Decimal("0.00"))
    return {
        "item_count": sum(item.quantity for item in items),
        "total_price": str(total_price),
        "items": [
            {
                "id": item.component_id,
                "name": item.component.name,
                "category": item.component.category.name,
                "quantity": item.quantity,
                "price": str(item.component.price),
                "line_total": str(item.component.price * item.quantity),
            }
            for item in items
        ],
        "compatibility": check_compatibility(items) if items else {"is_valid": True, "errors": [], "warnings": []},
    }


@require_POST
def auth_login(request):
    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"success": False, "errors": ["Неверный логин или пароль."]}, status=400)

    login(request, user)
    _attach_session_build(request, user)
    return JsonResponse({"success": True, "username": user.username})


@require_POST
def auth_register(request):
    user_model = get_user_model()
    username = request.POST.get("username", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")
    password_confirm = request.POST.get("password_confirm", "")

    if not username or not password:
        return JsonResponse({"success": False, "errors": ["Заполните логин и пароль."]}, status=400)
    if password != password_confirm:
        return JsonResponse({"success": False, "errors": ["Пароли не совпадают."]}, status=400)
    if user_model.objects.filter(username__iexact=username).exists():
        return JsonResponse({"success": False, "errors": ["Этот логин уже занят."]}, status=400)

    try:
        validate_password(password)
    except ValidationError as error:
        return JsonResponse({"success": False, "errors": error.messages}, status=400)

    user = user_model.objects.create_user(username=username, email=email, password=password)
    login(request, user)
    _attach_session_build(request, user)
    return JsonResponse({"success": True, "username": user.username})


@require_POST
def auth_logout(request):
    logout(request)
    return redirect("component_catalog")


def _attach_session_build(request, user):
    build_id = request.session.get("active_build_id")
    build = Build.objects.filter(pk=build_id).first() if build_id else None
    if build is None or build.user_id == user.pk:
        return

    if build.user_id is None:
        build.user = user
        build.save(update_fields=["user"])
        return

    # Avoid transferring a build owned by a different account.
    new_build = Build.objects.create(user=user, title=build.title)
    BuildItem.objects.bulk_create(
        [
            BuildItem(build=new_build, component_id=item.component_id, quantity=item.quantity)
            for item in build.items.all()
        ]
    )
    request.session["active_build_id"] = new_build.pk


@require_http_methods(["GET", "POST"])
def checkout(request):
    if not request.user.is_authenticated:
        if request.method == "POST":
            return JsonResponse({"success": False, "errors": ["Войдите, чтобы оформить заказ."]}, status=401)
        return redirect(f"{reverse('component_catalog')}?auth=required&checkout=1")

    build = _get_active_build(request)
    if build is None or not build.items.exists():
        if request.method == "POST":
            return JsonResponse({"success": False, "errors": ["Текущая сборка пуста."]}, status=400)
        return redirect("component_catalog")

    if request.method == "GET":
        return redirect(f"{reverse('component_catalog')}?checkout=1")

    form = CheckoutForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors.get_json_data()}, status=400)

    items = list(build.items.select_related("component", "component__category"))
    total = sum((item.component.price * item.quantity for item in items), Decimal("0.00"))
    with transaction.atomic():
        order = UserOrder.objects.create(
            user=request.user,
            build=build,
            total_price=total,
            delivery_date=form.cleaned_data["delivery_date"],
            email=form.cleaned_data["email"],
        )
        UserOrderItem.objects.bulk_create(
            [
                UserOrderItem(
                    order=order,
                    component=item.component,
                    component_name=item.component.name,
                    unit_price=item.component.price,
                    quantity=item.quantity,
                )
                for item in items
            ]
        )
        build.status = Build.Status.ORDERED
        build.save(update_fields=["status"])
        build.items.all().delete()
        request.session.pop("active_build_id", None)

    component_lines = "\n".join(
        f"- {item.component.name} × {item.quantity}: {item.component.price * item.quantity:.2f} ₽"
        for item in items
    )
    email_body = (
        f"Заказ №{order.pk} оформлен.\n\n"
        f"Комплектующие:\n{component_lines}\n\n"
        f"Итого: {total:.2f} ₽\n"
        f"Дата доставки: {order.delivery_date:%d.%m.%Y}"
    )
    send_mail(
        subject=f"PCFORGE: заказ №{order.pk}",
        message=email_body,
        from_email=None,
        recipient_list=[order.email],
        fail_silently=False,
    )
    return JsonResponse(
        {
            "success": True,
            "order_id": order.pk,
            "message": f"Заказ №{order.pk} оформлен! Чек и детали отправлены на вашу почту.",
        }
    )


def component_create(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponseForbidden("Добавлять товары могут только сотрудники каталога.")

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


def _get_active_build(request):
    build_id = request.session.get("active_build_id")
    if not build_id:
        return None
    if request.user.is_authenticated:
        build = Build.objects.filter(pk=build_id).first()
        if build and build.user_id is None:
            build.user = request.user
            build.save(update_fields=["user"])
        if build and build.user_id == request.user.pk:
            return build
        return None
    return Build.objects.filter(pk=build_id, user__isnull=True).first()