from django.core.management.base import BaseCommand

from pcbuilder.models import Category


BASE_CATEGORIES = (
    ("processors", "Процессоры"),
    ("graphic-cards", "Видеокарты"),
    ("motherboards", "Материнские платы"),
    ("ram", "Оперативная память"),
    ("storage", "Накопители"),
    ("power-supplies", "Блоки питания"),
    ("cases", "Корпуса"),
    ("cooling", "Охлаждение"),
)


class Command(BaseCommand):
    help = "Create or update the default PC component categories."

    def handle(self, *args, **options):
        for slug, name in BASE_CATEGORIES:
            Category.objects.update_or_create(slug=slug, defaults={"name": name})
        self.stdout.write(self.style.SUCCESS(f"Ensured {len(BASE_CATEGORIES)} default categories."))