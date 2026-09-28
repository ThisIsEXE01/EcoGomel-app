from django.db import models

# класс для отходов
class WasteItem(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=200)

    code = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    recyclable = models.BooleanField()

    hazard_class = models.CharField(
        max_length=200,
        default=""
    )

    preparation_steps = models.JSONField(
        default=list
    )

    what_happens_next = models.TextField(
        default=""
    )

    keywords = models.JSONField(
        default=list
    )

    map_filter_category = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


#класс для пунктов приёма отходов
class DropoffPoint(models.Model):
    name = models.CharField(max_length=300)
    address = models.CharField(max_length=300)

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    working_hours = models.CharField(max_length=300)
    description = models.TextField(default="")

    accepted_types = models.ManyToManyField(
        WasteItem,
        blank=True,
        related_name="dropoff_points"
    )

    def __str__(self):
        return self.name

