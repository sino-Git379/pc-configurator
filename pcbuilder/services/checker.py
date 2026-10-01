from collections.abc import Iterable

from pcbuilder.models import Build, BuildItem, Component


def check_compatibility(build_or_items: Build | Iterable[BuildItem | Component]) -> dict:
    """Check a Build or its items and return errors and non-blocking warnings."""
    if isinstance(build_or_items, Build):
        items = list(build_or_items.items.select_related("component", "component__category"))
    else:
        items = list(build_or_items)

    entries = []
    for item in items:
        if isinstance(item, BuildItem):
            entries.append((item.component, item.quantity))
        elif isinstance(item, Component):
            entries.append((item, 1))
        else:
            raise TypeError("Expected Build, BuildItem, or Component instances.")

    errors: list[str] = []
    warnings: list[str] = []
    cpus = _components_in(entries, "cpu", "processor")
    motherboards = _components_in(entries, "motherboard", "mainboard")
    memory = _components_in(entries, "ram", "memory")
    gpus = _components_in(entries, "gpu", "graphics-card", "video-card")
    cases = _components_in(entries, "case", "pc-case", "chassis")
    coolers = _components_in(entries, "cooler", "cpu-cooler")
    power_supplies = _components_in(entries, "power-supply", "psu")

    for cpu, _ in cpus:
        cpu_socket = _spec(cpu, "socket")
        for motherboard, _ in motherboards:
            board_socket = _spec(motherboard, "socket")
            if cpu_socket and board_socket and _normalized(cpu_socket) != _normalized(board_socket):
                errors.append(f"Сокет CPU ({cpu_socket}) не совпадает с сокетом материнской платы ({board_socket}).")
            elif not cpu_socket or not board_socket:
                warnings.append("Не удалось проверить сокет: заполните socket у CPU и материнской платы.")

    for ram, _ in memory:
        ram_type = _spec(ram, "memory_type", "ram_type", "type")
        for motherboard, _ in motherboards:
            supported_types = _spec(motherboard, "supported_ram_types", "memory_types", "ram_type")
            if isinstance(supported_types, str):
                supported_types = supported_types.split(",")
            if ram_type and supported_types:
                supported = {_normalized(value) for value in supported_types}
                if _normalized(ram_type) not in supported:
                    errors.append(f"Тип RAM ({ram_type}) не поддерживается материнской платой.")
            elif not ram_type or not supported_types:
                warnings.append("Не удалось проверить тип RAM: укажите тип памяти и поддержку на плате.")

    _check_case_clearance(
        gpus, cases, "length_mm", "max_gpu_length_mm", "длина видеокарты", errors, warnings
    )
    _check_case_clearance(coolers, cases, "height_mm", "max_cooler_height_mm", "высота кулера", errors, warnings)

    required_power = 100
    has_power_data = True
    for cpu, quantity in cpus:
        tdp = _spec(cpu, "tdp")
        if tdp is None:
            has_power_data = False
        else:
            required_power += _as_number(tdp) * quantity
    for gpu, quantity in gpus:
        power_draw = _spec(gpu, "power_draw")
        if power_draw is None:
            has_power_data = False
        else:
            required_power += _as_number(power_draw) * quantity

    supply_capacity = 0
    has_supply_capacity = bool(power_supplies)
    for supply, quantity in power_supplies:
        wattage = _spec(supply, "wattage", "wattage_w", "power_w", "capacity_w")
        if wattage is None:
            has_supply_capacity = False
        else:
            supply_capacity += _as_number(wattage) * quantity

    if has_power_data and has_supply_capacity:
        if required_power > supply_capacity:
            errors.append(
                f"Требуемая мощность {required_power} Вт превышает мощность БП {supply_capacity:g} Вт."
            )
    else:
        warnings.append("Не удалось проверить мощность: заполните TDP, потребление GPU и мощность БП.")

    return {"is_valid": not errors, "errors": errors, "warnings": _unique(warnings)}


def _check_case_clearance(items, cases, component_key, case_key, label, errors=None, warnings=None):
    errors = errors if errors is not None else []
    warnings = warnings if warnings is not None else []
    for component, _ in items:
        size = _spec(component, component_key)
        for case, _ in cases:
            maximum = _spec(case, case_key)
            if size is not None and maximum is not None:
                if _as_number(size) > _as_number(maximum):
                    errors.append(f"{label.capitalize()} ({size} мм) превышает ограничение корпуса ({maximum} мм).")
            else:
                warnings.append(f"Не удалось проверить {label}: заполните характеристики компонента и корпуса.")


def _components_in(entries, *category_names):
    accepted = {_normalized(name).replace("_", "-") for name in category_names}
    return [
        (component, quantity)
        for component, quantity in entries
        if _normalized(component.category.slug).replace("_", "-") in accepted
        or _normalized(component.category.name).replace("_", "-") in accepted
    ]


def _spec(component, *keys):
    for key in keys:
        value = component.specs.get(key)
        if value is not None and value != "":
            return value
    return None


def _normalized(value):
    return str(value).strip().casefold()


def _as_number(value):
    return float(value)


def _unique(values):
    return list(dict.fromkeys(values))