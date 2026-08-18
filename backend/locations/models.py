from django.db import models


class Location(models.Model):
    class CityTier(models.TextChoices):
        BIG = "big", "Big"
        SMALL = "small", "Small"

    city_name = models.CharField(
        max_length=100,
        unique=True,
    )

    region = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    city_tier = models.CharField(
        max_length=10,
        choices=CityTier.choices,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.city_name
