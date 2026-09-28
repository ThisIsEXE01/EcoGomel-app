import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from waste.models import WasteItem


class Command(BaseCommand):
    help = "Импортирует отходы из data/waste.json"

    def handle(self, *args, **options):
        file_path = settings.BASE_DIR / "data" / "waste.json"

        if not file_path.exists():
            raise CommandError(f"Файл не найден: {file_path}")

        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        for item in data:
            WasteItem.objects.update_or_create(
                name=item["name"],
                defaults={
                    "category": item["category"],
                    "code": item.get("code"),
                    "recyclable": item["is_recyclable"],
                    "hazard_class": item.get("hazard_class", ""),
                    "preparation_steps": item.get("preparation_steps", []),
                    "what_happens_next": item.get("what_happens_next", ""),
                    "keywords": item.get("keywords", []),
                    "map_filter_category": item.get("map_filter_category"),
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Импортировано или обновлено записей: {len(data)}"
            )
        )