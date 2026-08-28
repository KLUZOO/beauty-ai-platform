from django.conf import settings
from django.db import models


class ReferralEvent(models.Model):
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="referral_events",
    )
    session_id = models.CharField(
        max_length=64,
    )
    salon = models.ForeignKey(
        "salons.Salon",
        on_delete=models.CASCADE,
        related_name="referral_events",
    )
    service = models.ForeignKey(
        "beauty_service.Service",
        on_delete=models.CASCADE,
        related_name="referral_events",
        null=True,
        blank=True,
    )
    source = models.CharField(
        max_length=120,
    )
    destination_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(
        max_length=20,
    )

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["session_id"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["salon"]),
            models.Index(fields=["service"]),
            models.Index(fields=["salon", "created_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.event_type} | "
            f"{self.salon.name} | "
            f"{self.created_at:%Y-%m-%d %H:%M:%S}"
        )
