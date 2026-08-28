from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models


class Review(models.Model):
    appointment = models.OneToOneField(
        "appointments.Appointment",
        related_name="review",
        on_delete=models.CASCADE,
    )
    # client = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     related_name="reviews_written",
    #     on_delete=models.CASCADE,
    # )
    # master = models.ForeignKey(
    #     "users.Master",
    #     related_name="reviews_received",
    #     on_delete=models.CASCADE,
    # )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews"
        constraints = (
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="reviews_rating_checks",
            ),
        )

    def __str__(self) -> str:
        return f"Review #{self.id} — {self.rating}/5 for {self.appointment.master}"
