"""API-тесты стабильности эндпоинтов.

Покрывают:
  GET /api/waste/
  GET /api/waste/<id>/
  GET /api/points/

Проверяется: коды ответов (200 / 400 / 404 / 405), формат JSON, набор полей,
работа фильтров, устойчивость к «мусорным» входным данным, отсутствие N+1
запросов и согласованность данных после реального импорта из data/*.json.

Тесты написаны на встроенном Django TestCase (как и остальные тесты проекта).
Запуск из папки backend:
  python manage.py test waste
"""

import io
import unittest
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from .models import DropoffPoint, WasteItem

WASTE_FIELDS = {
    "id",
    "name",
    "category",
    "code",
    "recyclable",
    "hazard_class",
    "preparation_steps",
    "what_happens_next",
    "keywords",
    "map_filter_category",
}

POINT_FIELDS = {
    "id",
    "name",
    "address",
    "latitude",
    "longitude",
    "working_hours",
    "description",
    "accepted_types",
}

NON_GET_METHODS = ("post", "put", "patch", "delete")


def make_waste(name, category="Пластик", **kwargs):
  """Создаёт отход; обязательные поля модели заполняются значениями по умолчанию."""
  kwargs.setdefault("recyclable", True)
  return WasteItem.objects.create(name=name, category=category, **kwargs)


def make_point(name, accepted=(), latitude="52.430000", longitude="30.970000"):
  """Создаёт пункт приёма и привязывает к нему отходы."""
  point = DropoffPoint.objects.create(
      name=name,
      address=f"г. Гомель, {name}",
      latitude=Decimal(latitude),
      longitude=Decimal(longitude),
      working_hours="Пн-Пт 09:00-18:00",
      description=f"Описание: {name}",
  )
  point.accepted_types.set(accepted)
  return point


class ApiTestCase(TestCase):
  """Общие проверки ответа для всех API-тестов."""

  def assert_json(self, response, status=200):
    self.assertEqual(response.status_code, status)
    self.assertEqual(response["Content-Type"], "application/json")
    return response.json()

  def assert_method_not_allowed(self, url):
    for method in NON_GET_METHODS:
      with self.subTest(method=method):
        response = getattr(self.client, method)(url)
        data = self.assert_json(response, 405)
        self.assertEqual(data, {"error": "Method not allowed"})


# --------------------------------------------------------------------------
# GET /api/waste/
# --------------------------------------------------------------------------
class WasteListApiTests(ApiTestCase):
  url = "/api/waste/"

  @classmethod
  def setUpTestData(cls):
    cls.pet = make_waste(
        "ПЭТ-бутылки",
        "Пластик",
        code="01 PET",
        keywords=["бутылка", "вода"],
        map_filter_category="Пластик",
    )
    cls.battery = make_waste(
        "Бытовые батарейки",
        "Опасные отходы",
        recyclable=False,
        map_filter_category="Батарейки",
    )
    cls.glass = make_waste("Стеклотара", "Стекло", code="70 GL")

  def ids(self, params=None):
    data = self.assert_json(self.client.get(self.url, params or {}))
    return [item["id"] for item in data]

  # --- коды и формат ---
  def test_returns_200_and_json_list_with_exact_fields(self):
    data = self.assert_json(self.client.get(self.url))

    self.assertIsInstance(data, list)
    self.assertEqual(len(data), 3)
    for item in data:
      self.assertEqual(set(item), WASTE_FIELDS)

  def test_empty_database_returns_empty_list(self):
    WasteItem.objects.all().delete()

    self.assertEqual(self.assert_json(self.client.get(self.url)), [])

  def test_cyrillic_is_not_escaped_in_body(self):
    response = self.client.get(self.url)

    self.assertIn("Пластик".encode("utf-8"), response.content)
    self.assertNotIn(b"\\u", response.content)

  def test_repeated_requests_return_identical_response(self):
    first = self.client.get(self.url).content

    for _ in range(3):
      self.assertEqual(self.client.get(self.url).content, first)

  def test_list_uses_single_query(self):
    with self.assertNumQueries(1):
      self.client.get(self.url)

  def test_non_get_methods_return_405(self):
    self.assert_method_not_allowed(self.url)

  # --- фильтры ---
  def test_filter_by_category(self):
    self.assertEqual(self.ids({"category": "Пластик"}), [self.pet.id])
    self.assertEqual(self.ids({"category": "Стекло"}), [self.glass.id])

  @unittest.expectedFailure
  def test_filter_by_category_ignores_case_for_cyrillic(self):
    """Известная проблема: SQLite iexact не учитывает регистр кириллицы.

    category=пластик не находит «Пластик». Когда это починят, тест начнёт
    «неожиданно проходить» — тогда нужно убрать декоратор expectedFailure.
    """
    self.assertEqual(self.ids({"category": "пластик"}), [self.pet.id])

  def test_filter_by_code(self):
    self.assertEqual(self.ids({"code": "01"}), [self.pet.id])
    self.assertEqual(self.ids({"code": "GL"}), [self.glass.id])

  def test_filter_by_recyclable_accepts_true_false_1_0(self):
    recyclable = [self.pet.id, self.glass.id]

    for value in ("true", "True", "1"):
      with self.subTest(value=value):
        self.assertEqual(self.ids({"recyclable": value}), recyclable)

    for value in ("false", "FALSE", "0"):
      with self.subTest(value=value):
        self.assertEqual(self.ids({"recyclable": value}), [self.battery.id])

  def test_invalid_recyclable_value_is_ignored_not_400(self):
    """Фиксирует текущее поведение: мусор в recyclable не даёт 400."""
    self.assertEqual(len(self.ids({"recyclable": "maybe"})), 3)

  def test_combined_filters(self):
    self.assertEqual(
        self.ids({"category": "Пластик", "recyclable": "true", "code": "PET"}),
        [self.pet.id],
    )
    self.assertEqual(
        self.ids({"category": "Пластик", "recyclable": "false"}), []
    )

  def test_filters_without_matches_return_empty_list(self):
    for params in (
        {"category": "Несуществующая"},
        {"code": "zzz"},
        {"search": "кракозябра"},
    ):
      with self.subTest(params=params):
        self.assertEqual(self.assert_json(self.client.get(self.url, params)), [])

  def test_blank_or_too_short_search_does_not_filter(self):
    for value in ("", "   ", "...", "а"):
      with self.subTest(search=value):
        self.assertEqual(len(self.ids({"search": value})), 3)

  def test_search_finds_item(self):
    self.assertEqual(self.ids({"search": "бутылка"}), [self.pet.id])

  def test_unknown_query_params_are_ignored(self):
    self.assertEqual(len(self.ids({"foo": "bar", "page": "999"})), 3)

  # --- устойчивость к странному вводу ---
  def test_weird_search_input_never_breaks_endpoint(self):
    weird = [
        "%",
        "_",
        "'",
        '"',
        "\\",
        "'; DROP TABLE waste_wasteitem; --",
        "<script>alert(1)</script>",
        "🙂♻️",
        "а" * 2000,
        "слово " * 200,
        "\x00",
    ]

    for value in weird:
      with self.subTest(search=value[:30]):
        data = self.assert_json(self.client.get(self.url, {"search": value}))
        self.assertIsInstance(data, list)

    self.assertEqual(WasteItem.objects.count(), 3)


# --------------------------------------------------------------------------
# GET /api/waste/<id>/
# --------------------------------------------------------------------------
class WasteDetailApiTests(ApiTestCase):

  @classmethod
  def setUpTestData(cls):
    cls.item = make_waste(
        "ПЭТ-бутылки",
        "Пластик",
        code="01 PET",
        hazard_class="Безопасные отходы",
        preparation_steps=["Ополоснуть", "Сжать"],
        what_happens_next="Дробится во флексу.",
        keywords=["бутылка", "вода"],
        map_filter_category="Пластик",
    )

  def url(self, pk):
    return f"/api/waste/{pk}/"

  def test_returns_200_with_exact_fields_and_stored_values(self):
    data = self.assert_json(self.client.get(self.url(self.item.id)))

    self.assertEqual(set(data), WASTE_FIELDS)
    self.assertEqual(data["id"], self.item.id)
    self.assertEqual(data["name"], "ПЭТ-бутылки")
    self.assertEqual(data["category"], "Пластик")
    self.assertEqual(data["code"], "01 PET")
    self.assertIs(data["recyclable"], True)
    self.assertEqual(data["hazard_class"], "Безопасные отходы")
    self.assertEqual(data["preparation_steps"], ["Ополоснуть", "Сжать"])
    self.assertEqual(data["what_happens_next"], "Дробится во флексу.")
    self.assertEqual(data["keywords"], ["бутылка", "вода"])
    self.assertEqual(data["map_filter_category"], "Пластик")

  def test_nullable_fields_are_returned_as_null(self):
    bare = make_waste("Без кода", "Прочее")

    data = self.assert_json(self.client.get(self.url(bare.id)))

    self.assertIsNone(data["code"])
    self.assertIsNone(data["map_filter_category"])
    self.assertEqual(data["preparation_steps"], [])
    self.assertEqual(data["keywords"], [])

  def test_detail_matches_list_entry(self):
    listed = self.assert_json(self.client.get("/api/waste/"))[0]
    detail = self.assert_json(self.client.get(self.url(self.item.id)))

    self.assertEqual(detail, listed)

  def test_missing_id_returns_404_json(self):
    for pk in (0, self.item.id + 1000, 99999999999999999999):
      with self.subTest(pk=pk):
        data = self.assert_json(self.client.get(self.url(pk)), 404)
        self.assertEqual(data, {"error": "Waste item not found"})

  def test_deleted_item_returns_404(self):
    pk = self.item.id
    self.assert_json(self.client.get(self.url(pk)))

    WasteItem.objects.filter(pk=pk).delete()

    data = self.assert_json(self.client.get(self.url(pk)), 404)
    self.assertEqual(data, {"error": "Waste item not found"})

  def test_non_integer_ids_return_404(self):
    """Маршрут принимает только целые неотрицательные id, остальное — 404."""
    for pk in ("abc", "-1", "1.5", "1e3", "%D0%B0"):
      with self.subTest(pk=pk):
        self.assertEqual(self.client.get(self.url(pk)).status_code, 404)

  def test_detail_uses_single_query(self):
    with self.assertNumQueries(1):
      self.client.get(self.url(self.item.id))

  def test_non_get_methods_return_405(self):
    self.assert_method_not_allowed(self.url(self.item.id))


# --------------------------------------------------------------------------
# GET /api/points/
# --------------------------------------------------------------------------
class PointsApiStabilityTests(ApiTestCase):
  url = "/api/points/"

  @classmethod
  def setUpTestData(cls):
    cls.pet = make_waste("ПЭТ-бутылки", "Пластик", map_filter_category="Пластик")
    cls.hdpe = make_waste("Плотный полиэтилен", "Пластик")
    cls.battery = make_waste(
        "Батарейки", "Опасные отходы", map_filter_category="Батарейки"
    )
    cls.unused = make_waste("Шины", "Крупногабаритные отходы")

    cls.plastic_point = make_point(
        "Пункт пластика", [cls.pet, cls.hdpe], "52.417200", "30.916800"
    )
    cls.mixed_point = make_point("Пункт смешанный", [cls.pet, cls.battery])
    cls.battery_point = make_point("Пункт батареек", [cls.battery])
    cls.empty_point = make_point("Пункт без отходов")

  def ids(self, params=None):
    data = self.assert_json(self.client.get(self.url, params or {}))
    return [point["id"] for point in data]

  # --- коды и формат ---
  def test_returns_200_and_json_list_with_exact_fields(self):
    data = self.assert_json(self.client.get(self.url))

    self.assertIsInstance(data, list)
    self.assertEqual(len(data), 4)
    for point in data:
      self.assertEqual(set(point), POINT_FIELDS)

  def test_empty_database_returns_empty_list(self):
    DropoffPoint.objects.all().delete()

    self.assertEqual(self.assert_json(self.client.get(self.url)), [])

  def test_field_types_are_leaflet_friendly(self):
    point = self.assert_json(self.client.get(self.url))[0]

    self.assertIsInstance(point["id"], int)
    self.assertIsInstance(point["latitude"], float)
    self.assertIsInstance(point["longitude"], float)
    self.assertAlmostEqual(point["latitude"], 52.4172, places=4)
    self.assertAlmostEqual(point["longitude"], 30.9168, places=4)
    self.assertIsInstance(point["accepted_types"], list)

  def test_points_are_ordered_by_id(self):
    ids = self.ids()

    self.assertEqual(ids, sorted(ids))

  def test_repeated_requests_return_identical_response(self):
    first = self.client.get(self.url).content

    for _ in range(3):
      self.assertEqual(self.client.get(self.url).content, first)

  def test_accepted_types_are_unique_sorted_categories(self):
    by_id = {
        p["id"]: p for p in self.assert_json(self.client.get(self.url))
    }

    # У «Плотного полиэтилена» нет map_filter_category -> берётся category,
    # дубликат «Пластик» схлопывается.
    self.assertEqual(
        by_id[self.plastic_point.id]["accepted_types"], ["Пластик"]
    )
    self.assertEqual(
        by_id[self.mixed_point.id]["accepted_types"], ["Батарейки", "Пластик"]
    )
    self.assertEqual(by_id[self.empty_point.id]["accepted_types"], [])

  def test_cyrillic_is_not_escaped_in_body(self):
    response = self.client.get(self.url)

    self.assertIn("Пункт пластика".encode("utf-8"), response.content)
    self.assertNotIn(b"\\u", response.content)

  def test_non_get_methods_return_405(self):
    self.assert_method_not_allowed(self.url)

  def test_query_count_does_not_depend_on_number_of_points(self):
    """Защита от N+1: всегда 2 запроса (пункты + prefetch отходов)."""
    with self.assertNumQueries(2):
      self.client.get(self.url)

    for i in range(10):
      make_point(f"Дополнительный {i}", [self.pet, self.battery])

    with self.assertNumQueries(2):
      self.client.get(self.url)
    with self.assertNumQueries(2):
      self.client.get(self.url, {"waste_id": self.pet.id})

  # --- фильтр waste_id: 200 ---
  def test_filter_by_waste_id(self):
    self.assertEqual(
        self.ids({"waste_id": self.pet.id}),
        [self.plastic_point.id, self.mixed_point.id],
    )
    self.assertEqual(
        self.ids({"waste_id": self.battery.id}),
        [self.mixed_point.id, self.battery_point.id],
    )

  def test_filter_keeps_all_categories_of_matching_point(self):
    data = self.assert_json(
        self.client.get(self.url, {"waste_id": self.pet.id})
    )
    by_id = {p["id"]: p for p in data}

    self.assertEqual(
        by_id[self.mixed_point.id]["accepted_types"], ["Батарейки", "Пластик"]
    )

  def test_filter_never_returns_duplicates(self):
    """Пункт принимает два вида пластика, но в выдаче он один раз."""
    ids = self.ids({"waste_id": self.hdpe.id})

    self.assertEqual(ids, [self.plastic_point.id])
    self.assertEqual(len(ids), len(set(ids)))

  def test_filter_for_waste_without_points_returns_empty_list(self):
    self.assertEqual(self.ids({"waste_id": self.unused.id}), [])

  def test_filter_for_nonexistent_waste_returns_empty_list_not_404(self):
    for value in ("0", "-1", "999999", "99999999999999999999"):
      with self.subTest(waste_id=value):
        self.assertEqual(self.ids({"waste_id": value}), [])

  def test_blank_waste_id_is_ignored(self):
    self.assertEqual(len(self.ids({"waste_id": ""})), 4)
    self.assertEqual(len(self.ids({"waste_id": "   "})), 4)

  def test_whitespace_around_waste_id_is_trimmed(self):
    self.assertEqual(
        self.ids({"waste_id": f"  {self.battery.id} "}),
        [self.mixed_point.id, self.battery_point.id],
    )

  # --- фильтр waste_id: 400 ---
  def test_non_integer_waste_id_returns_400_json(self):
    for value in ("abc", "1.5", "1,5", "1e3", "0x1", "null", "1;DROP", "\x00", "—"):
      with self.subTest(waste_id=value):
        data = self.assert_json(
            self.client.get(self.url, {"waste_id": value}), 400
        )
        self.assertEqual(
            data, {"error": "waste_id должен быть целым числом"}
        )

  def test_400_error_message_is_not_escaped(self):
    response = self.client.get(self.url, {"waste_id": "abc"})

    self.assertIn("целым числом".encode("utf-8"), response.content)

  def test_400_does_not_touch_data(self):
    self.client.get(self.url, {"waste_id": "abc"})

    self.assertEqual(DropoffPoint.objects.count(), 4)
    self.assertEqual(len(self.ids()), 4)

  # --- 404 ---
  def test_unknown_subpaths_return_404(self):
    for path in ("/api/points/1/", "/api/points/abc/", "/api/point/", "/api/pointz/"):
      with self.subTest(path=path):
        self.assertEqual(self.client.get(path).status_code, 404)


# --------------------------------------------------------------------------
# Маршрутизация
# --------------------------------------------------------------------------
class ApiRoutingTests(ApiTestCase):

  @classmethod
  def setUpTestData(cls):
    cls.item = make_waste("ПЭТ-бутылки")

  def test_missing_trailing_slash_redirects_to_canonical_url(self):
    cases = {
        "/api/waste": "/api/waste/",
        f"/api/waste/{self.item.id}": f"/api/waste/{self.item.id}/",
        "/api/points": "/api/points/",
    }

    for url, expected in cases.items():
      with self.subTest(url=url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], expected)

  def test_unknown_api_paths_return_404(self):
    for url in ("/api/", "/api/unknown/", "/api/waste/1/2/", "/api/v1/points/"):
      with self.subTest(url=url):
        self.assertEqual(self.client.get(url).status_code, 404)


# --------------------------------------------------------------------------
# Реальные данные из data/*.json (интеграционные проверки)
# --------------------------------------------------------------------------
class ImportedDataApiTests(ApiTestCase):
  """После import_waste и import_dropoff_points API отдаёт согласованные данные."""

  @classmethod
  def setUpTestData(cls):
    quiet = io.StringIO()
    call_command("import_waste", stdout=quiet)
    call_command("import_dropoff_points", stdout=quiet)

  def test_waste_list_contains_all_imported_items(self):
    data = self.assert_json(self.client.get("/api/waste/"))

    self.assertGreater(len(data), 0)
    self.assertEqual(len(data), WasteItem.objects.count())
    for item in data:
      self.assertEqual(set(item), WASTE_FIELDS)
      self.assertTrue(item["name"])
      self.assertTrue(item["category"])
      self.assertIsInstance(item["preparation_steps"], list)
      self.assertIsInstance(item["keywords"], list)

  def test_every_waste_detail_returns_200_and_matches_list(self):
    listed = self.assert_json(self.client.get("/api/waste/"))

    for item in listed:
      with self.subTest(id=item["id"]):
        detail = self.assert_json(self.client.get(f"/api/waste/{item['id']}/"))
        self.assertEqual(detail, item)

  def test_points_list_contains_all_imported_points(self):
    data = self.assert_json(self.client.get("/api/points/"))

    self.assertGreater(len(data), 0)
    self.assertEqual(len(data), DropoffPoint.objects.count())

  def test_every_point_has_valid_content_and_coordinates_in_gomel_area(self):
    for point in self.assert_json(self.client.get("/api/points/")):
      with self.subTest(id=point["id"]):
        self.assertEqual(set(point), POINT_FIELDS)
        self.assertTrue(point["name"])
        self.assertTrue(point["address"])
        self.assertTrue(point["working_hours"])
        self.assertTrue(point["accepted_types"])
        # Защита от перепутанных широты и долготы.
        self.assertTrue(52.0 < point["latitude"] < 53.0)
        self.assertTrue(30.5 < point["longitude"] < 31.5)

  def test_waste_id_filter_matches_database_relations_for_every_waste(self):
    covered = set()

    for waste in WasteItem.objects.all():
      with self.subTest(waste_id=waste.id):
        data = self.assert_json(
            self.client.get("/api/points/", {"waste_id": waste.id})
        )
        expected = set(
            DropoffPoint.objects.filter(accepted_types=waste).values_list(
                "id", flat=True
            )
        )
        ids = [p["id"] for p in data]

        self.assertEqual(set(ids), expected)
        self.assertEqual(len(ids), len(set(ids)))
        covered |= expected

    self.assertEqual(covered, set(DropoffPoint.objects.values_list("id", flat=True)))

  def test_repeated_import_does_not_change_api_output(self):
    before = (
        self.client.get("/api/waste/").content,
        self.client.get("/api/points/").content,
    )

    quiet = io.StringIO()
    call_command("import_waste", stdout=quiet)
    call_command("import_dropoff_points", stdout=quiet)

    after = (
        self.client.get("/api/waste/").content,
        self.client.get("/api/points/").content,
    )
    self.assertEqual(before, after)
