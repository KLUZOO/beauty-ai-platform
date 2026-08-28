"""
ЧЕРНЕТКА для обговорення — куди ділити ці моделі по apps.
Побудовано за структурою з beauty_line_db_2.sql (Ihor).
Не є частиною робочого проекту, просто для звірки.
"""

from django.db import models


class Salon(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    district = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    opened_date = models.DateField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'salons'

    def __str__(self):
        return self.name


class ServiceCategory(models.Model):
    name = models.CharField(max_length=60)

    class Meta:
        db_table = 'service_categories'

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(
        ServiceCategory,
        related_name='services',
        on_delete=models.CASCADE,
        db_column='category_id',
    )
    name = models.CharField(max_length=120)
    duration_minutes = models.PositiveSmallIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        db_table = 'services'
        constraints = [
            models.CheckConstraint(
                check=models.Q(duration_minutes__gt=0),
                name='services_duration_minutes_check',
            ),
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name='services_price_check',
            ),
        ]

    def __str__(self):
        return self.name
