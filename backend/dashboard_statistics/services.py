from django.db.models import (
    Avg,
    Sum
)
from django.utils import timezone
from payments.models import Payment
from users.models import Master


class StatisticsService:
    @staticmethod
    def get_master_statistics(master: Master):
        today = timezone.localdate()

        appointments = master.appointments.all()
        total_appointments = appointments.count()

        # Replaced appointment_date__gt with start__date__gt
        upcoming_appointments = appointments.filter(
            start__date__gt=today,
            status="confirmed",
        ).count()
        completed_appointments = appointments.filter(
            status="completed",
        ).count()
        cancelled_appointments = appointments.filter(
            status="cancelled",
        ).count()

        # Replaced appointment_date with start__date
        today_appointments = appointments.filter(
            start__date=today,
            status__in=["confirmed", "completed"],
        ).count()

        payments = Payment.objects.filter(
            appointment__master=master,
            appointment__status="completed",
            payment_status="completed",
        )
        total_earnings = payments.aggregate(total=Sum("amount"))["total"] or 0

        # Replaced appointment__appointment_date with appointment__start
        monthly_earnings = (
                payments.filter(
                    appointment__start__year=today.year,
                    appointment__start__month=today.month,
                ).aggregate(total=Sum("amount"))["total"]
                or 0
        )

        reviews = master.appontments.review.all()
        total_reviews = reviews.count()
        average_rating = (
            reviews.aggregate(average=Avg("rating"))["average"]
            if total_reviews > 0
            else 0.0
        )

        number_of_active_services = master.services.filter(is_active=True).count()
        total_clients = (
            appointments.filter(status="completed").values("client").distinct().count()
        )

        return {
            "total_appointments": total_appointments,
            "upcoming_appointments": upcoming_appointments,
            "completed_appointments": completed_appointments,
            "cancelled_appointments": cancelled_appointments,
            "today_appointments": today_appointments,
            "total_earnings": total_earnings,
            "monthly_earnings": monthly_earnings,
            "average_rating": average_rating,
            "total_reviews": total_reviews,
            "number_of_active_services": number_of_active_services,
            "total_clients": total_clients,
        }
