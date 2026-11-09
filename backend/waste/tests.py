from django.test import TestCase
from .models import WasteItem


class WasteSearchMorphologyTests(TestCase):

  def setUp(self):
    self.item1 = WasteItem.objects.create(
        name="Пластиковая бутылка",
        code="PET-01",
        category="Пластик",
        recyclable=True,
    )
    self.item2 = WasteItem.objects.create(
        name="Литиевая батарейка",
        code="BAT-02",
        category="Опасные отходы",
        recyclable=False,
    )

  def test_search_wordforms_plural_and_singular(self):
    """Проверка поиска по разным словоформам (бутылка / бутылки, батарейка / батарейки)."""
    response = self.client.get("/api/waste/?search=бутылки")
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertTrue(any(item["id"] == self.item1.id for item in data))

    response = self.client.get("/api/waste/?search=батарейки")
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertTrue(any(item["id"] == self.item2.id for item in data))

  def test_search_by_code_intact(self):
    """Проверка, что поиск по коду не сломался."""
    response = self.client.get("/api/waste/?search=PET-01")
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(len(data), 1)
    self.assertEqual(data[0]["id"], self.item1.id)

  def test_search_by_category_intact(self):
    """Проверка, что поиск по категории не сломался."""
    response = self.client.get("/api/waste/?search=Пластик")
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertGreaterEqual(len(data), 1)