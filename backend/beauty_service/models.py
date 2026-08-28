import os
from uuid import uuid4

from django.db import models


def generate_upload_path(instance, filename) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return f"services/{uuid4()}{ext}"


class ServiceCategory(models.Model):
    name = models.CharField(max_length=60)

    class Meta:
        db_table = "service_categories"

    def __str__(self) -> str:
        return self.name


class Service(models.Model):
    category = models.ForeignKey(
        ServiceCategory,
        related_name="services",
        on_delete=models.CASCADE,
        db_column="category_id",
    )
    name = models.CharField(max_length=120)
    duration_minutes = models.PositiveSmallIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to=generate_upload_path,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "services"
        constraints = (
            models.CheckConstraint(
                condition=models.Q(duration_minutes__gt=0),
                name="services_duration_minutes_checks",
            ),
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="services_price_checks",
            ),
        )

    def __str__(self) -> str:
        return self.name
