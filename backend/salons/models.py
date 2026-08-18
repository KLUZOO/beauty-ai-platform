from django.conf import settings
from django.db import models
from django.db.models import F, Q
from locations.models import Location

from .services import generate_upload_path


class SalonStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    PENDING = "pending", "Pending"


class AbstractSalon(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(Location, null=True, on_delete=models.SET_NULL)
    district = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=150)
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    opened_date = models.DateField(
        null=True,
        blank=True,
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    external_booking_url = models.URLField(
        null=True,
        blank=True,
    )
    description = models.TextField(
        null=True,
        blank=True,
    )
    logo = models.ImageField(
        upload_to=generate_upload_path,
    )
    available_status = models.CharField(
        max_length=20,
    )
    salon_status = models.CharField(
        max_length=20,
        choices=SalonStatus.choices,
        default=SalonStatus.PENDING,
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name


class Salon(AbstractSalon):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="salons",
        null=True,
        blank=True,
    )
    masters = models.ManyToManyField(
        "users.Master",
        through="users.MasterSalon",
        related_name="salons",
    )

    class Meta:
        db_table = "salons"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "address"], name="unique_partner_salon_name_address"
            ),
        ]


class CachedSalon(AbstractSalon):
    last_used_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )
    opening_hours = models.JSONField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "cached_salons"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "address"], name="unique_cached_salon_name_address"
            ),
        ]


class SalonWorkingHours(models.Model):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    WEEKDAY_CHOICES = [
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THURSDAY, "Thursday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday"),
    ]

    salon = models.ForeignKey(
        Salon,
        related_name="working_hours",
        on_delete=models.CASCADE,
    )
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
    is_closed = models.BooleanField(default=False)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = "salon_working_hours"
        constraints = [
            models.UniqueConstraint(
                fields=["salon", "weekday"],
                name="unique_salon_weekday",
            ),
            models.CheckConstraint(
                condition=(
                    Q(is_closed=True)
                    | (
                        Q(opening_time__isnull=False)
                        & Q(closing_time__isnull=False)
                        & Q(opening_time__lt=F("closing_time"))
                    )
                ),
                name="valid_salon_working_hours",
            ),
        ]

    # noinspection PyUnresolvedReferences
    def __str__(self) -> str:
        if self.is_closed:
            return f"{self.salon.name} — {self.get_weekday_display()}: closed"
        return f"{self.salon.name} — {self.get_weekday_display()}: {self.opening_time}-{self.closing_time}"
