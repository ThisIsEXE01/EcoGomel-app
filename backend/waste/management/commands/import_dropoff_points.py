import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from waste.models import DropoffPoint, WasteItem


# Соответствие названий из dropoff_points.json
# с конкретными видами отходов из WasteItem.
ACCEPTED_TYPES = {
    "Пластик": [
        "ПЭТ-бутылки (прозрачный пластик)",
        "Плотный полиэтилен (флаконы, канистры)",
        "Полиэтилен низкой плотности (пакеты, пленка)",
        "Полипропилен (стаканчики, упаковка)",
    ],
    "Пластик PET": [
        "ПЭТ-бутылки (прозрачный пластик)",
    ],
    "Полимеры": [
        "ПЭТ-бутылки (прозрачный пластик)",
        "Плотный полиэтилен (флаконы, канистры)",
        "Полиэтилен низкой плотности (пакеты, пленка)",
        "Полипропилен (стаканчики, упаковка)",
    ],
    "Полимерные отходы": [
        "ПЭТ-бутылки (прозрачный пластик)",
        "Плотный полиэтилен (флаконы, канистры)",
        "Полиэтилен низкой плотности (пакеты, пленка)",
        "Полипропилен (стаканчики, упаковка)",
    ],
    "Макулатура": [
        "Макулатура (бумага, картон)",
    ],
    "Стекло": [
        "Стеклотара и стеклобой",
    ],
    "Стеклобой": [
        "Стеклотара и стеклобой",
    ],
    "Стеклотара": [
        "Стеклотара и стеклобой",
    ],
    "Металлолом": [
        "Черный металл (жесть, консервы)",
        "Алюминий (банки от напитков)",
    ],
    "Батарейки": [
        "Бытовые батарейки и аккумуляторы",
    ],
    "Аккумуляторы": [
        "Автомобильный аккумулятор (АКБ)",
    ],
    "Ртутные лампы": [
        "Энергосберегающие и ртутные лампы",
    ],
    "Электроника": [
        "Бытовая техника и электроника",
    ],
    "Бытовая техника": [
        "Бытовая техника и электроника",
    ],
    "Изношенные шины": [
        "Автомобильные шины (покрышки)",
    ],
    "Крупногабаритные отходы": [
        "Автомобильные шины (покрышки)",
    ],
    "Текстиль": [
        "Текстиль и старая одежда",
    ],
}


class Command(BaseCommand):
    help = "Импортирует пункты приема из data/dropoff_points.json"

    def handle(self, *args, **options):
        file_path = settings.BASE_DIR / "data" / "dropoff_points.json"

        if not file_path.exists():
            raise CommandError(f"Файл не найден: {file_path}")

        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        for item in data:
            point, created = DropoffPoint.objects.update_or_create(
                id=item["id"],
                defaults={
                    "name": item["name"],
                    "address": item["address"],
                    "latitude": item["latitude"],
                    "longitude": item["longitude"],
                    "working_hours": item["working_hours"],
                    "description": item["description"],
                },
            )

            waste_items = []

            for accepted_type in item["accepted_types"]:
                if accepted_type not in ACCEPTED_TYPES:
                    raise CommandError(
                        f"Неизвестный тип отходов: {accepted_type}"
                    )

                names = ACCEPTED_TYPES[accepted_type]

                for name in names:
                    try:
                        waste_item = WasteItem.objects.get(name=name)
                    except WasteItem.DoesNotExist:
                        raise CommandError(
                            f"Отход не найден в базе: {name}"
                        )

                    waste_items.append(waste_item)

            point.accepted_types.set(waste_items)

        self.stdout.write(
            self.style.SUCCESS(
                f"Импортировано или обновлено пунктов: {len(data)}"
            )
        )