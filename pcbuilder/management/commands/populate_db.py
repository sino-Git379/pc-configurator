from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from pcbuilder.management.commands.pc_component_data import CATEGORY_THUMBNAILS, COMPONENTS
from pcbuilder.management.commands.seed_categories import BASE_CATEGORIES
from pcbuilder.models import Category, Component


class Command(BaseCommand):
    help = "Replace seeded PC components with 15 category-correct products per category."

    def handle(self, *args, **options):
        expected_categories = {slug for slug, _ in BASE_CATEGORIES}
        if set(COMPONENTS) != expected_categories or set(CATEGORY_THUMBNAILS) != expected_categories:
            raise CommandError("Seed products, categories, and thumbnail URL maps must use the same slugs.")

        with transaction.atomic():
            deleted_count, _ = Component.objects.all().delete()
            categories = {
                slug: Category.objects.update_or_create(slug=slug, defaults={"name": name})[0]
                for slug, name in BASE_CATEGORIES
            }
            created_count = 0

            for category_slug, products in COMPONENTS.items():
                category = categories[category_slug]
                thumbnail = CATEGORY_THUMBNAILS[category_slug]
                if len(products) != 15:
                    raise CommandError(f"Category {category_slug} must contain exactly 15 products.")

                for name, price, specs in products:
                    Component.objects.create(
                        category=category,
                        name=name,
                        price=price,
                        specs=specs,
                        thumbnail_url=thumbnail["url"],
                        thumbnail_source_url=thumbnail["source_url"],
                        thumbnail_credit=thumbnail["credit"],
                    )
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Populate complete: removed {deleted_count} components and created "
                f"{created_count} with category-matched image URLs. No network downloads performed."
            )
        )