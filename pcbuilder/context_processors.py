from decimal import Decimal

from django.utils import timezone

from .models import Build
from .services.checker import check_compatibility


def current_build(request):
    build_id = request.session.get("active_build_id")
    builds = (
        Build.objects.filter(user=request.user, status=Build.Status.DRAFT)
        if request.user.is_authenticated
        else Build.objects.none()
    )
    if build_id and request.user.is_authenticated:
        build = Build.objects.filter(pk=build_id, user=request.user).first()
    elif build_id:
        build = Build.objects.filter(pk=build_id, user__isnull=True).first()
    else:
        build = None
    items = list(build.items.select_related("component", "component__category") if build else [])
    return {
        "current_build": build,
        "current_build_items": items,
        "current_build_component_ids": [item.component_id for item in items],
        "user_builds": builds.order_by("-created_at")[:20],
        "min_delivery_date": timezone.localdate().isoformat(),
        "current_build_count": sum(item.quantity for item in items),
        "current_build_total": sum(
            (item.component.price * item.quantity for item in items), Decimal("0.00")
        ),
        "current_build_compatibility": check_compatibility(items)
        if items
        else {"is_valid": True, "errors": [], "warnings": []},
    }