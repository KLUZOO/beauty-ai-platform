from django.contrib.gis.db import models


class Location(models.Model):
    class CityTier(models.TextChoices):
        BIG = "big", "Big"
        SMALL = "small", "Small"

    country = models.CharField(
        max_length=100,
    )

    city_name = models.CharField(
        max_length=100,
    )

    address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    region = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    coordinates = models.PointField(
        srid=4326,
        geography=True,
        null=True,
        blank=True,
    )

    timezone = models.CharField(
        max_length=64,
        default="UTC",
    )

    city_tier = models.CharField(
        max_length=5,
        choices=CityTier.choices,
        null=True,
        blank=True,
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("country", "city_name", "address"),
                name="unique_location_address",
            ),
        )

    def __str__(self) -> str:
        return f"{self.city_name}, {self.country}"
