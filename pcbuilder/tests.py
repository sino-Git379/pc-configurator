from django.test import TestCase
from django.urls import reverse

from pcbuilder.forms import ComponentForm
from pcbuilder.models import Build, BuildItem, Category, Component
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

        response = self.client.get(reverse("component_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PCFORGE")
        self.assertContains(response, 'data-slug="cpu"')
        self.assertContains(response, "/static/pcbuilder/component_form.css")
        self.assertContains(response, "/static/pcbuilder/component_form.js")

    def test_post_saves_component_specs_and_redirects(self):
        category = Category.objects.create(name="CPU", slug="cpu")

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
        self.assertContains(response, 'href="?category=cpu"')
        self.assertContains(response, '"base_clock": "3.8 GHz"')

    def test_component_can_be_added_and_quantity_and_total_are_updated(self):
        url = reverse("add_component_to_build", args=[self.component.pk])

        first_response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        second_response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.json()["item_count"], 1)
        self.assertEqual(second_response.json()["total_price"], "499.98")
        self.assertEqual(BuildItem.objects.get().quantity, 2)


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