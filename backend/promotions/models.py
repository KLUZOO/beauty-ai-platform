from django.core.validators import MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models


class Promotion(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    discount_percent = models.PositiveIntegerField(
        validators=[
            MaxValueValidator(100),
        ]
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    salon = models.ForeignKey(
        'salons.Salon',
        on_delete=models.CASCADE,
        related_name="promotions",
    )

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
        indexes = [
            models.Index(fields=["start_date", "end_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["salon", "name"],
                name="unique_promotion_name_per_salon",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if (
                self.start_date
                and self.end_date
                and self.start_date >= self.end_date
        ):
            raise ValidationError(
                {"end_date": "The end date must be later than the start date."}
            )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.discount_percent}%) - "
            f"{self.salon.name} "
            f"[{self.start_date} – {self.end_date}]"
        )
