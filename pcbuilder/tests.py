import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from pcbuilder.forms import ComponentForm
from pcbuilder.management.commands.pc_component_data import CATEGORY_THUMBNAILS, COMPONENTS
from pcbuilder.models import Build, BuildItem, Category, Component, UserOrder, UserOrderItem
from pcbuilder.services.checker import check_compatibility


class ComponentFormTests(TestCase):
    def test_specs_json_is_saved_as_object(self):
        category = Category.objects.create(name="CPU", slug="cpu")
        form = ComponentForm(
            data={
                "category": category.pk,
                "name": "Test CPU",
                "price": "100.00",
                "specs_json": '{"socket":"AM5","tdp":65}',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().specs, {"socket": "AM5", "tdp": 65})

    def test_specs_json_must_be_an_object(self):
        category = Category.objects.create(name="CPU", slug="cpu")
        form = ComponentForm(
            data={
                "category": category.pk,
                "name": "Test CPU",
                "price": "100.00",
                "specs_json": '["AM5"]',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("specs_json", form.errors)


class ComponentCreateViewTests(TestCase):
    def test_get_renders_pcforge_layout_and_category_slug(self):
        Category.objects.create(name="CPU", slug="cpu")
        staff = get_user_model().objects.create_user(username="catalog-staff", password="test-pass-123", is_staff=True)
        self.client.force_login(staff)

        response = self.client.get(reverse("component_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PCFORGE")
        self.assertContains(response, 'data-slug="cpu"')
        self.assertContains(response, "/static/pcbuilder/component_form.css")
        self.assertContains(response, "/static/pcbuilder/component_form.js")

    def test_post_saves_component_specs_and_redirects(self):
        category = Category.objects.create(name="CPU", slug="cpu")
        staff = get_user_model().objects.create_user(username="catalog-writer", password="test-pass-123", is_staff=True)
        self.client.force_login(staff)

        response = self.client.post(
            "/components/new/",
            {
                "category": category.pk,
                "name": "Test CPU",
                "price": "100.00",
                "specs_json": '{"socket":"AM5","tdp":65}',
            },
        )

        self.assertRedirects(response, "/components/new/")
        component = Component.objects.get(name="Test CPU")
        self.assertEqual(component.specs, {"socket": "AM5", "tdp": 65})

    def test_component_create_rejects_guest_and_non_staff_with_403(self):
        url = reverse("component_create")
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {}).status_code, 403)

        user = get_user_model().objects.create_user(username="regular-user", password="test-pass-123")
        self.client.force_login(user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {}).status_code, 403)


class ComponentCatalogTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="CPU", slug="cpu")
        self.component = Component.objects.create(
            category=self.category,
            name="Test Processor",
            price="249.99",
            specs={"socket": "AM5", "cores": 8, "base_clock": "3.8 GHz"},
        )

    def test_catalog_renders_component_catalog_data_and_category(self):
        response = self.client.get(reverse("component_catalog"), {"category": "cpu"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Processor")
        self.assertContains(response, 'href="/?category=cpu&amp;sort=popular"')
        self.assertContains(response, '"base_clock": "3.8 GHz"')
        self.assertContains(response, "class=\"card-add\"")
        self.assertContains(response, "id=\"auth-modal\"")
        self.assertContains(response, "id=\"cart-modal\"")
        self.assertContains(response, "id=\"cart-open\"")
        self.assertNotContains(response, "id=\"add-to-build\"")

    def test_component_can_be_added_and_quantity_and_total_are_updated(self):
        url = reverse("add_component_to_build", args=[self.component.pk])

        first_response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        second_response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.json()["item_count"], 2)
        self.assertEqual(second_response.json()["total_price"], "499.98")
        self.assertEqual(
            second_response.json()["items"],
            [{
                "id": self.component.pk,
                "name": "Test Processor",
                "category": "CPU",
                "quantity": 2,
                "price": "249.99",
                "line_total": "499.98",
            }],
        )
        self.assertEqual(BuildItem.objects.get().quantity, 2)

        catalog_page = self.client.get(reverse("component_catalog"), {"category": "cpu"})
        self.assertContains(catalog_page, "Test Processor")
        self.assertContains(catalog_page, "499,98")

        staff = get_user_model().objects.create_user(username="catalog-viewer", password="test-pass-123", is_staff=True)
        self.client.force_login(staff)
        form_page = self.client.get(reverse("component_create"))
        self.assertEqual(form_page.status_code, 200)
        self.assertContains(form_page, "КОМПЛЕКТУЮЩИЕ")
        self.assertNotContains(form_page, "Test Processor")
        self.assertNotContains(form_page, "ТЕКУЩАЯ СБОРКА")

    def test_component_can_be_removed_from_session_cart(self):
        add_url = reverse("add_component_to_build", args=[self.component.pk])
        remove_url = reverse("remove_component_from_build", args=[self.component.pk])
        self.client.post(add_url)

        response = self.client.post(remove_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["item_count"], 0)
        self.assertEqual(response.json()["items"], [])
        self.assertTrue(response.json()["compatibility"]["is_valid"])
        self.assertFalse(BuildItem.objects.exists())

    def test_category_thumbnail_url_is_used_in_preview_payload(self):
        self.component.thumbnail_url = "https://example.test/ram-dimm.jpg"
        self.component.save(update_fields=["thumbnail_url"])

        response = self.client.get(reverse("component_catalog"), {"category": "cpu"})

        self.assertEqual(response.context["component_data"][0]["thumbnail"], self.component.thumbnail_url)

    def test_catalog_sorting_orders_prices_and_popularity(self):
        cheapest = Component.objects.create(category=self.category, name="Cheap", price="50.00")
        most_expensive = Component.objects.create(category=self.category, name="Expensive", price="700.00")
        popular = Component.objects.create(category=self.category, name="Popular", price="300.00")
        build = Build.objects.create(title="Popularity")
        BuildItem.objects.create(build=build, component=popular, quantity=5)
        BuildItem.objects.create(build=build, component=cheapest, quantity=2)

        popular_response = self.client.get(reverse("component_catalog"), {"sort": "popular"})
        ascending_response = self.client.get(reverse("component_catalog"), {"sort": "price_asc"})
        descending_response = self.client.get(reverse("component_catalog"), {"sort": "price_desc"})

        self.assertEqual(
            list(popular_response.context["components"].values_list("name", flat=True))[:3],
            ["Popular", "Cheap", "Expensive"],
        )
        self.assertEqual(
            list(ascending_response.context["components"].values_list("name", flat=True))[:3],
            ["Cheap", "Test Processor", "Popular"],
        )
        self.assertEqual(
            list(descending_response.context["components"].values_list("name", flat=True))[:3],
            ["Expensive", "Popular", "Test Processor"],
        )

    def test_active_build_filter_shows_only_saved_components_and_can_be_reset(self):
        other = Component.objects.create(category=self.category, name="Not in build", price="20.00")
        user = get_user_model().objects.create_user(username="filter-user", password="test-pass-123")
        build = Build.objects.create(user=user, title="Filtered build")
        BuildItem.objects.create(build=build, component=self.component)
        session = self.client.session
        session["active_build_id"] = build.pk
        session.save()
        self.client.force_login(user)

        filtered = self.client.get(reverse("component_catalog"), {"build": "active"})
        reset = self.client.get(reverse("component_catalog"))

        self.assertEqual(list(filtered.context["components"]), [self.component])
        self.assertContains(filtered, "Показать все товары")
        self.assertContains(filtered, "build=active")
        self.assertEqual(set(reset.context["components"]), {self.component, other})


class CompatibilityCheckerTests(TestCase):
    def setUp(self):
        self.categories = {
            slug: Category.objects.create(name=name, slug=slug)
            for slug, name in [
                ("cpu", "CPU"),
                ("motherboard", "Motherboard"),
                ("ram", "RAM"),
                ("gpu", "GPU"),
                ("case", "Case"),
                ("cooler", "Cooler"),
                ("power-supply", "Power Supply"),
            ]
        }

    def component(self, category, specs):
        return Component.objects.create(
            category=self.categories[category], name=category, price="100.00", specs=specs
        )

    def test_compatible_build_passes(self):
        build = Build.objects.create(title="Compatible build")
        components = [
            self.component("cpu", {"socket": "AM5", "tdp": 120}),
            self.component("motherboard", {"socket": "AM5", "supported_ram_types": ["DDR5"]}),
            self.component("ram", {"memory_type": "DDR5"}),
            self.component("gpu", {"length_mm": 300, "power_draw": 250}),
            self.component("case", {"max_gpu_length_mm": 330, "max_cooler_height_mm": 160}),
            self.component("cooler", {"height_mm": 150}),
            self.component("power-supply", {"wattage": 750}),
        ]
        BuildItem.objects.bulk_create([BuildItem(build=build, component=component) for component in components])

        result = check_compatibility(build)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["errors"], [])

    def test_incompatible_build_reports_each_constraint(self):
        components = [
            self.component("cpu", {"socket": "AM4", "tdp": 200}),
            self.component("motherboard", {"socket": "AM5", "supported_ram_types": ["DDR5"]}),
            self.component("ram", {"memory_type": "DDR4"}),
            self.component("gpu", {"length_mm": 350, "power_draw": 500}),
            self.component("case", {"max_gpu_length_mm": 320, "max_cooler_height_mm": 140}),
            self.component("cooler", {"height_mm": 155}),
            self.component("power-supply", {"wattage": 650}),
        ]

        result = check_compatibility(components)

        self.assertFalse(result["is_valid"])
        self.assertEqual(len(result["errors"]), 5)

    def test_build_item_quantities_are_included_in_power_check(self):
        build = Build.objects.create(title="Quantity check")
        cpu = self.component("cpu", {"tdp": 100})
        power_supply = self.component("power-supply", {"wattage": 250})
        BuildItem.objects.create(build=build, component=cpu, quantity=2)
        BuildItem.objects.create(build=build, component=power_supply)

        result = check_compatibility(build)

        self.assertFalse(result["is_valid"])
        self.assertTrue(any("мощность" in error for error in result["errors"]))

    def test_default_plural_category_slugs_are_checked(self):
        processor_category = Category.objects.create(name="Processors", slug="processors")
        board_category = Category.objects.create(name="Motherboards", slug="motherboards")
        processor = Component.objects.create(
            category=processor_category, name="Processor", price="100.00", specs={"socket": "AM4", "tdp": 65}
        )
        board = Component.objects.create(
            category=board_category, name="Board", price="100.00", specs={"socket": "AM5"}
        )

        result = check_compatibility([processor, board])

        self.assertFalse(result["is_valid"])
        self.assertTrue(any("Сокет CPU" in error for error in result["errors"]))


class SeedCategoryCommandTests(TestCase):
    def test_command_creates_default_categories_idempotently(self):
        call_command("seed_categories", verbosity=0)
        call_command("seed_categories", verbosity=0)

        self.assertEqual(Category.objects.count(), 8)
        self.assertEqual(Category.objects.get(slug="processors").name, "Процессоры")
        self.assertEqual(Category.objects.get(slug="graphic-cards").name, "Видеокарты")


class PopulateDBCommandTests(TestCase):
    def test_command_creates_120_components_with_lowercase_numeric_specs_idempotently(self):
        call_command("populate_db", verbosity=0)

        self.assertEqual(Category.objects.count(), 8)
        self.assertEqual(Component.objects.count(), 120)
        self.assertEqual(Category.objects.get(slug="ram").name, "Оперативная память")
        for component in Component.objects.all():
            self.assertTrue(all(key == key.lower() for key in component.specs))
            json.dumps(component.specs, allow_nan=False)
            for key, value in component.specs.items():
                if key in {
                    "cores", "threads", "tdp", "length_mm", "power_draw", "vram_gb",
                    "memory_bus_bit", "capacity_gb", "speed_mhz", "cas_latency", "modules",
                    "read_speed_mbps", "write_speed_mbps", "power_w", "max_gpu_length_mm",
                    "max_cooler_height_mm", "max_radiator_mm", "drive_bays_35", "height_mm",
                    "tdp_capacity_w",
                }:
                    self.assertIsInstance(value, (int, float), f"{component.name}: {key}")
                    self.assertNotIsInstance(value, bool, f"{component.name}: {key}")
            expected_image = CATEGORY_THUMBNAILS[component.category.slug]
            self.assertEqual(component.thumbnail_url, expected_image["url"])
            self.assertEqual(component.thumbnail_source_url, expected_image["source_url"])

        self.assertEqual({slug: len(products) for slug, products in COMPONENTS.items()}, {slug: 15 for slug in COMPONENTS})

    def test_command_clears_old_components_and_never_requests_images(self):
        category = Category.objects.create(name="Old", slug="old")
        stale_component = Component.objects.create(category=category, name="Stale", price="1.00")
        build = Build.objects.create(title="Old build")
        BuildItem.objects.create(build=build, component=stale_component)

        with patch("socket.create_connection", side_effect=AssertionError("populate_db must not access the network")) as create_connection:
            call_command("populate_db", verbosity=0)

        create_connection.assert_not_called()
        self.assertEqual(Component.objects.count(), 120)
        self.assertFalse(Component.objects.filter(pk=stale_component.pk).exists())
        self.assertFalse(BuildItem.objects.filter(build=build).exists())


class AuthorizationAndCheckoutTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Processors", slug="processors")
        component = Component.objects.create(category=category, name="CPU", price="199.00")
        self.build = Build.objects.create(title="My current build")
        BuildItem.objects.create(build=self.build, component=component, quantity=2)
        session = self.client.session
        session["active_build_id"] = self.build.pk
        session.save()

    def test_login_authenticates_and_attaches_current_session_build(self):
        user = get_user_model().objects.create_user(username="builder", password="test-pass-123")

        response = self.client.post(
            reverse("auth_login"),
            {"username": "builder", "password": "test-pass-123"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True, "username": "builder"})
        self.build.refresh_from_db()
        self.assertEqual(self.build.user, user)


    def test_registration_authenticates_and_attaches_current_session_build(self):
        response = self.client.post(
            reverse("auth_register"),
            {
                "username": "new-builder",
                "email": "builder@example.com",
                "password": "test-pass-123",
                "password_confirm": "test-pass-123",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True, "username": "new-builder"})
        self.build.refresh_from_db()
        self.assertEqual(self.build.user.username, "new-builder")
        self.assertEqual(self.build.items.get().quantity, 2)

    def test_checkout_requires_auth_and_renders_saved_build_for_user(self):
        checkout_url = reverse("checkout")
        anonymous_response = self.client.get(checkout_url)
        self.assertRedirects(anonymous_response, f"/?auth=required&checkout=1")

        user = get_user_model().objects.create_user(username="customer", password="test-pass-123", email="customer@example.com")
        self.client.force_login(user)
        response = self.client.get(checkout_url)

        self.assertRedirects(response, "/?checkout=1")
        self.build.refresh_from_db()
        self.assertEqual(self.build.user, user)

    def test_checkout_creates_order_snapshots_emails_and_clears_session_cart(self):
        user = get_user_model().objects.create_user(username="order-user", password="test-pass-123", email="order@example.com")
        self.client.force_login(user)
        delivery_date = timezone.localdate() + timedelta(days=7)

        with override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            response = self.client.post(
                reverse("checkout"),
            {"delivery_date": delivery_date.isoformat(), "email": "receipt@example.com"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertIn("Заказ №", response.json()["message"])
        order = UserOrder.objects.get()
        self.assertEqual(order.user, user)
        self.assertEqual(order.build, self.build)
        self.assertEqual(order.total_price, Decimal("398.00"))
        self.assertEqual(order.delivery_date, delivery_date)
        order_item = UserOrderItem.objects.get(order=order)
        self.assertEqual((order_item.component_name, order_item.quantity), ("CPU", 2))
        self.assertEqual(order_item.unit_price, Decimal("199.00"))
        self.assertEqual(order.build.status, Build.Status.ORDERED)
        self.assertFalse(BuildItem.objects.filter(build=self.build).exists())
        self.assertNotIn("active_build_id", self.client.session)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("CPU × 2", mail.outbox[0].body)
        self.assertIn("398.00 ₽", mail.outbox[0].body)
        self.assertIn(delivery_date.strftime("%d.%m.%Y"), mail.outbox[0].body)

    def test_checkout_rejects_past_delivery_date_and_save_build_marks_draft(self):
        user = get_user_model().objects.create_user(username="draft-user", password="test-pass-123")
        self.client.force_login(user)
        self.build.user = user
        self.build.save(update_fields=["user"])

        saved = self.client.post(reverse("save_build"))
        invalid_order = self.client.post(
            reverse("checkout"),
            {"delivery_date": "2020-01-01", "email": "draft@example.com"},
        )

        self.assertEqual(saved.status_code, 200)
        self.build.refresh_from_db()
        self.assertEqual(self.build.status, Build.Status.DRAFT)
        self.assertEqual(invalid_order.status_code, 400)
        self.assertFalse(UserOrder.objects.exists())

    def test_authenticated_quick_add_claims_existing_session_build(self):
        user = get_user_model().objects.create_user(username="signed-in", password="test-pass-123")
        self.client.force_login(user)
        component = self.build.items.first().component

        response = self.client.post(reverse("add_component_to_build", args=[component.pk]))

        self.assertEqual(response.status_code, 200)
        self.build.refresh_from_db()
        self.assertEqual(self.build.user, user)
        self.assertEqual(self.build.items.get().quantity, 3)

    def test_logout_uses_django_auth_and_redirects(self):
        user = get_user_model().objects.create_user(username="logout-user", password="test-pass-123")
        self.client.force_login(user)

        response = self.client.post(reverse("auth_logout"))

        self.assertRedirects(response, reverse("component_catalog"))
        catalog_response = self.client.get(reverse("component_catalog"))
        self.assertContains(catalog_response, "data-open-auth")

    def test_account_navbar_shows_login_or_profile_on_each_page(self):
        guest_page = self.client.get(reverse("component_catalog"))
        self.assertContains(guest_page, "data-open-auth")
        self.assertContains(guest_page, "Войти / Регистрация")

        user = get_user_model().objects.create_user(username="sino-profile", password="test-pass-123", is_staff=True)
        self.client.force_login(user)
        for url in (reverse("component_catalog"), reverse("component_create"), reverse("checkout")):
            page = self.client.get(url, follow=True)
            self.assertContains(page, "sino-profile")
            self.assertContains(page, "ONLINE")
            self.assertContains(page, reverse("auth_logout"))

    def test_login_validation_returns_errors_array(self):
        response = self.client.post(
            reverse("auth_login"),
            {"username": "missing", "password": "wrong"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Неверный логин", response.json()["errors"][0])


class SavedBuildNavigationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="builder-nav", password="test-pass-123")
        category = Category.objects.create(name="Processors", slug="processors")
        self.cpu = Component.objects.create(category=category, name="CPU nav", price="100.00")
        self.first_build = Build.objects.create(user=self.user, title="Игровой ПК 2026")
        self.second_build = Build.objects.create(user=self.user, title="Рабочая станция")
        BuildItem.objects.create(build=self.first_build, component=self.cpu)
        session = self.client.session
        session["active_build_id"] = self.first_build.pk
        session.save()

    def test_guest_sidebar_prompts_login_and_has_no_duplicate_build_cart(self):
        response = self.client.get(reverse("component_catalog"))

        self.assertContains(response, "КОМПЛЕКТУЮЩИЕ")
        self.assertContains(response, "МОИ СБОРКИ")
        self.assertContains(response, "Войти, чтобы увидеть сборки")
        self.assertNotContains(response, "ТЕКУЩАЯ СБОРКА")

    def test_sidebar_renders_accordion_and_marks_active_build_component(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("component_catalog"))

        self.assertContains(response, "КОМПЛЕКТУЮЩИЕ")
        self.assertContains(response, "МОИ СБОРКИ")
        self.assertContains(response, "Игровой ПК 2026")
        self.assertContains(response, "Рабочая станция")
        self.assertContains(response, 'class="product-card is-in-build"')
        self.assertContains(response, "В этой сборке")
        self.assertNotContains(response, "ТЕКУЩАЯ СБОРКА")

    def test_user_can_select_owned_build_and_catalog_highlights_its_parts(self):
        second_cpu = Component.objects.create(category=self.cpu.category, name="Second CPU nav", price="200.00")
        BuildItem.objects.create(build=self.second_build, component=second_cpu)
        self.client.force_login(self.user)
        response = self.client.post(reverse("select_build", args=[self.second_build.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"success": True, "build_id": self.second_build.pk, "build_title": "Рабочая станция"},
        )
        self.assertEqual(self.client.session["active_build_id"], self.second_build.pk)
        catalog = self.client.get(reverse("component_catalog"), {"build": "active"})
        highlighted = {
            product["name"]: product["is_in_build"]
            for product in catalog.context["component_data"]
        }
        self.assertEqual(
            list(catalog.context["components"].values_list("name", flat=True)),
            ["Second CPU nav"],
        )
        self.assertTrue(highlighted["Second CPU nav"])
        self.assertContains(catalog, 'class="product-card is-in-build"')

    def test_guest_cannot_select_saved_build_or_see_other_users_builds(self):
        response = self.client.post(reverse("select_build", args=[self.first_build.pk]))
        self.assertEqual(response.status_code, 401)

        other_user = get_user_model().objects.create_user(username="other-nav", password="test-pass-123")
        self.client.force_login(other_user)
        forbidden = self.client.post(reverse("select_build", args=[self.first_build.pk]))
        self.assertEqual(forbidden.status_code, 404)
        catalog = self.client.get(reverse("component_catalog"))
        self.assertNotContains(catalog, "Игровой ПК 2026")
        self.assertEqual(self.client.session["active_build_id"], self.first_build.pk)