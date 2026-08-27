from django.conf import settings
from django.db import models


class LinkTracking(models.Model):
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="link_tracking_events",
    )

    session_id = models.CharField(
        max_length=64,
        db_index=True,
    )

    salon = models.ForeignKey(
        "salons.Salon",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="link_tracking_events",
    )

    service = models.ForeignKey(
        "beauty_service.Service",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="link_tracking_events",
    )

    source = models.CharField(
        max_length=120,
    )

    destination_url = models.URLField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    event_type = models.CharField(
        max_length=20,
    )

    class Meta:
        indexes = (
            models.Index(fields=["created_at"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["salon", "created_at"]),
        )

    def __str__(self) -> str:
        return (
            f"{self.event_type} | "
            f"{self.salon.name if self.salon else 'Unknown salon'} | "
            f"{self.created_at:%Y-%m-%d %H:%M:%S}"
        )


class ReferralProgram(models.Model):
    class RewardStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        EARNED = "earned", "Earned"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    referral_id = models.CharField(
        max_length=64,
        unique=True,
    )

    referring_client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referrals_sent",
    )

    referred_client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referral_received",
    )

    event_date = models.DateTimeField()

    reward_status = models.CharField(
        max_length=20,
        choices=RewardStatus.choices,
        default=RewardStatus.PENDING,
    )
