from django.conf import settings

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

from django.db import models
from django.db.models import (
    Avg,
    QuerySet
)

from django.utils import timezone
from django.utils.translation import gettext as _

from phonenumber_field.modelfields import PhoneNumberField

from .managers import UserManager
from .services.media_path import generate_upload_path


class GenderChoice(models.TextChoices):
    MAN = "man", "Man"
    WOMAN = "woman", "Woman"


class User(AbstractUser):
    username = None
    first_name = models.CharField(
        _("first name"),
        max_length=150,
    )
    last_name = models.CharField(
        _("last name"),
        max_length=150,
    )
    email = models.EmailField(_("email address"), unique=True)
    phone = PhoneNumberField(
        unique=True,
    )
    photo = models.ImageField(
        upload_to=generate_upload_path,
        null=True,
        blank=True,
    )
    google_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
    )
    gender = models.CharField(
        max_length=10,
        choices=GenderChoice.choices,
        blank=True,
        null=True,
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
    )
    preferred_salons = models.ManyToManyField(
        "salons.Salon",
        blank=True,
        related_name="followers",
    )
    last_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    last_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    registration_date_user = models.DateTimeField(
        auto_now_add=True,
    )
    last_update_user = models.DateTimeField(
        auto_now=True,
    )

    @property
    def is_master(self) -> bool:
        """Check if user has an associated master profile."""
        return hasattr(self, "master")

    def clean(self) -> None:
        """Validate user profile data."""
        super().clean()

        # Prevent setting future birth dates
        if self.birth_date and self.birth_date > timezone.now().date():
            raise ValidationError(
                {"birth_date": ["Birth date cannot be in the future."]}
            )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ()

    objects = UserManager()

    def __str__(self) -> str:
        return (
            f"{self.get_full_name()} ({self.email})"
            if self.get_full_name()
            else self.email
        )


class MasterStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    BLOCKED = "blocked", "Blocked"
    DELETED = "deleted", "Deleted"
    PENDING = "pending", "Pending"


class Master(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="master",
    )
    specialization = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    services = models.ManyToManyField(
        "beauty_service.Service",
        through="MasterService",
        related_name="masters",
    )
    bio = models.TextField(
        null=True,
        blank=True,
    )
    years_of_experience = models.PositiveIntegerField()
    registration_date_master = models.DateTimeField(
        auto_now_add=True,
    )
    last_update_master = models.DateTimeField(
        auto_now=True,
    )
    account_status = models.CharField(
        max_length=20,
        choices=MasterStatus.choices,
        default=MasterStatus.PENDING,
    )

    @property
    def active_services(self) -> QuerySet:
        """Return active services offered by the master."""
        return self.services.filter(is_active=True)

    @property
    def average_rating(self) -> float:
        """Calculate average rating, returning 0.0 if no reviews exist."""
        avg = self.appointments.review.aggregate(average=Avg("rating"))["average"]
        return round(avg, 2) if avg is not None else 0.0

    @property
    def total_reviews(self) -> int:
        """Return total number of reviews received by the master."""
        return self.appointments.review.count()

    @property
    def is_independent(self) -> bool:
        """Check if master is independent (not linked to any salon)."""
        return not self.salons.exists()

    def __str__(self) -> str:
        name = self.user.get_full_name() or self.user.email
        return f"{name} — {self.specialization}" if self.specialization else name


class WeekDay(models.IntegerChoices):
    MONDAY = 1, "Monday"
    TUESDAY = 2, "Tuesday"
    WEDNESDAY = 3, "Wednesday"
    THURSDAY = 4, "Thursday"
    FRIDAY = 5, "Friday"
    SATURDAY = 6, "Saturday"
    SUNDAY = 7, "Sunday"


class WorkingSchedule(models.Model):
    """Represents a master's recurring weekly working schedule for a specific day of the week."""

    master = models.ForeignKey(
        "Master",
        on_delete=models.CASCADE,
        related_name="working_schedule",
    )
    weekday = models.PositiveSmallIntegerField(
        choices=WeekDay.choices,
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
    )
    is_working_day = models.BooleanField(default=True)

    def clean(self) -> None:
        """Validate working schedule consistency and prevent overlapping shifts."""
        super().clean()

        # Block 1: Handle days off (ensure no working hours are set when is_working_day is False)
        if not self.is_working_day:
            if self.start_time or self.end_time:
                raise ValidationError(
                    {"non_field_errors": ["Day off cannot contain working hours."]}
                )
            return

        # Block 2: Ensure start_time and end_time are provided for active working days
        if self.start_time is None:
            raise ValidationError(
                {
                    "start_time": ["This field is required."],
                }
            )

        if self.end_time is None:
            raise ValidationError(
                {
                    "end_time": ["This field is required."],
                }
            )

        # Block 3: Validate logical sequence of time (start time must precede end time)
        if self.start_time >= self.end_time:
            raise ValidationError(
                {
                    "start_time": ["Start time must be earlier than end time."],
                    "end_time": ["End time must be later than start time."],
                }
            )

        # Block 4: Check for time range overlaps with existing schedules for the same master & weekday
        overlapping = WorkingSchedule.objects.filter(
            master=self.master,
            weekday=self.weekday,
            is_working_day=True,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        )

        # Exclude the current instance if updating an existing record
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError(
                {
                    "non_field_errors": [
                        "Working schedule overlaps with an existing schedule."
                    ],
                }
            )

    class Meta:
        ordering = ("weekday", "start_time")

    def __str__(self) -> str:
        """Return a human-readable representation of the working schedule."""
        if not self.is_working_day:
            return f"{self.master} - {self.get_weekday_display()} (Day off)"

        return (
            f"{self.master} - "
            f"{self.get_weekday_display()} "
            f"{self.start_time}-{self.end_time}"
        )


class DayOff(models.Model):
    """Represents a master's vacation, sick leave, or personal day off range."""

    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        related_name="days_off",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(
        max_length=255,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self) -> None:
        """Validate that end_date is not earlier than start_date."""
        super().clean()

        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(
                {"end_date": ["End date cannot be earlier than start date."]}
            )

    class Meta:
        ordering = ("start_date",)

    def __str__(self) -> str:
        """Return string representation of the day off range."""
        return f"{self.master} off: {self.start_date} to {self.end_date}"


class MasterSalon(models.Model):
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        related_name="master_salons",
    )
    salon = models.ForeignKey(
        "salons.Salon",
        on_delete=models.CASCADE,
        related_name="master_salons",
    )
    hire_date = models.DateField(
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=["master", "salon"],
                name="unique_master_salon",
            ),
        )

    def __str__(self) -> str:
        return f"{self.master} @ {self.salon}"


class MasterService(models.Model):
    master = models.ForeignKey(
        "Master",
        on_delete=models.CASCADE,
        related_name="master_services",
    )

    service = models.ForeignKey(
        "beauty_service.Service",
        on_delete=models.CASCADE,
        related_name="master_services",
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=["master", "service"],
                name="unique_master_service",
            ),
        )

    def __str__(self) -> str:
        return f"{self.master} - {self.service}"
