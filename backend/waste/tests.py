from decimal import Decimal

from django.test import TestCase

from .models import DropoffPoint, WasteItem


class PointsApiTests(TestCase):
    def setUp(self):
        self.pet = WasteItem.objects.create(
            name="ПЭТ-бутылки",
            category="Пластик",
            recyclable=True,
            map_filter_category="Пластик",
        )
        self.hdpe = WasteItem.objects.create(
            name="Плотный полиэтилен",
            category="Пластик",
            recyclable=True,
            map_filter_category=None,
        )
        self.battery = WasteItem.objects.create(
            name="Батарейки",
            category="Опасные отходы",
            recyclable=True,
            map_filter_category="Батарейки",
        )

        self.point = DropoffPoint.objects.create(
            name="Пункт на Барыкина",
            address="г. Гомель, ул. Барыкина, 299",
            latitude=Decimal("52.417200"),
            longitude=Decimal("30.916800"),
            working_hours="Пн-Пт 08:00-20:00",
            description="Тестовый пункт",
        )
        self.point.accepted_types.set([self.pet, self.hdpe, self.battery])

    def test_returns_empty_list_without_points(self):
        DropoffPoint.objects.all().delete()

        response = self.client.get("/api/points/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_returns_points_in_leaflet_format(self):
        response = self.client.get("/api/points/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = response.json()
        self.assertEqual(len(data), 1)

        point = data[0]
        self.assertEqual(point["id"], self.point.id)
        self.assertEqual(point["name"], "Пункт на Барыкина")
        self.assertEqual(point["address"], "г. Гомель, ул. Барыкина, 299")
        self.assertEqual(point["work_hours"], "Пн-Пт 08:00-20:00")
        self.assertEqual(
            set(point),
            {"id", "name", "address", "latitude", "longitude",
             "work_hours", "description", "accepted_types"},
        )
        self.assertEqual(point["description"], "Тестовый пункт")

    def test_coordinates_are_numbers(self):
        point = self.client.get("/api/points/").json()[0]

        self.assertIsInstance(point["latitude"], float)
        self.assertIsInstance(point["longitude"], float)
        self.assertAlmostEqual(point["latitude"], 52.4172, places=4)
        self.assertAlmostEqual(point["longitude"], 30.9168, places=4)

    def test_accepted_types_are_unique_filter_categories(self):
        point = self.client.get("/api/points/").json()[0]

        # у «Плотного полиэтилена» нет map_filter_category -> берётся category,
        # дубликат «Пластик» схлопывается
        self.assertEqual(point["accepted_types"], ["Батарейки", "Пластик"])

    def test_point_without_accepted_types(self):
        DropoffPoint.objects.create(
            name="Пустой пункт",
            address="г. Гомель",
            latitude=Decimal("52.430000"),
            longitude=Decimal("30.970000"),
            working_hours="Круглосуточно",
        )

        data = self.client.get("/api/points/").json()

        self.assertEqual(len(data), 2)
        self.assertEqual(data[1]["accepted_types"], [])

    def _create_other_point(self):
        other = DropoffPoint.objects.create(
            name="Пункт батареек",
            address="г. Гомель, ул. Ефремова, 11-1",
            latitude=Decimal("52.461800"),
            longitude=Decimal("30.965800"),
            working_hours="Пн-Вс 09:00-22:00",
        )
        other.accepted_types.set([self.battery])
        return other

    def test_filter_by_waste_id(self):
        other = self._create_other_point()

        data = self.client.get(f"/api/points/?waste_id={self.battery.id}").json()
        self.assertEqual({p["id"] for p in data}, {self.point.id, other.id})

        data = self.client.get(f"/api/points/?waste_id={self.pet.id}").json()
        self.assertEqual([p["id"] for p in data], [self.point.id])

    def test_filter_keeps_all_accepted_types_of_point(self):
        data = self.client.get(f"/api/points/?waste_id={self.pet.id}").json()

        self.assertEqual(data[0]["accepted_types"], ["Батарейки", "Пластик"])

    def test_filter_without_matches_returns_empty_list(self):
        response = self.client.get("/api/points/?waste_id=999999")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_filter_with_invalid_waste_id(self):
        response = self.client.get("/api/points/?waste_id=abc")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_only_get_is_allowed(self):
        response = self.client.post("/api/points/")

        self.assertEqual(response.status_code, 405)
