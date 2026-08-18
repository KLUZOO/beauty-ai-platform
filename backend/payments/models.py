from django.db import models


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    CARD = "card", "Card"
    APPLE_PAY = "apple_pay", "Apple Pay"
    GOOGLE_PAY = "google_pay", "Google Pay"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"


class Payment(models.Model):
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="UAH")
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    payment_date = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self) -> str:
        return (
            f"Appointment #{self.appointment_id} - "
            f"{self.amount} {self.currency} "
            f"({self.get_payment_method_display()}, "
            f"{self.get_payment_status_display()})"
        )

class Commission(models.Model):
    class PayerType(models.TextChoices):
        SOLO_MASTER = "solo_master", "Solo master"
        SALON = "salon", "Salon"

    appointment = models.OneToOneField(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        related_name="commission",
    )

    payer_type = models.CharField(
        max_length=20,
        choices=PayerType.choices,
    )

    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=3,
    )

    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    def __str__(self):
        return f"{self.commission_amount} — {self.payer_type}"
