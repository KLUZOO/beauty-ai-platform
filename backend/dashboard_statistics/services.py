from appointments.models import Appointment
from django.contrib.auth import get_user_model
from django.db.models import Avg, Sum
from django.utils import timezone
from payments.models import Payment, PaymentStatus
from users.models import Master, MasterStatus

User = get_user_model()


class StatisticsService:
    @staticmethod
    def get_admin_statistics(admin: User):
        today = timezone.localdate()

        clients_current = User.objects.filter(
            is_active=True,
            registration_date_user__date__gt=today - timezone.timedelta(days=30),
        ).count()
        revenue_current = (
            Payment.objects.filter(
                payment_status=PaymentStatus.COMPLETED,
                payment_date__date__gt=today - timezone.timedelta(days=30),
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        revenue_previous = (
            Payment.objects.filter(
                payment_status=PaymentStatus.COMPLETED,
                payment_date__date__gt=today - timezone.timedelta(days=60),
                payment_date__date__lte=today - timezone.timedelta(days=30),
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        clients_previous = User.objects.filter(
            is_active=True,
            registration_date_user__date__gt=today - timezone.timedelta(days=60),
            registration_date_user__date__lte=today - timezone.timedelta(days=30),
        ).count()
        masters_current = Master.objects.filter(
            account_status=MasterStatus.ACTIVE,
            last_update_master__date__gt=today - timezone.timedelta(days=30),
        ).count()
        masters_previous = Master.objects.filter(
            account_status=MasterStatus.INACTIVE,
            last_update_master__date__gt=today - timezone.timedelta(days=60),
            last_update_master__date__lte=today - timezone.timedelta(days=30),
        ).count()
        bookings = Appointment.objects.filter(
            status__in=["Confirmed", "Completed"],
        )
        bookings_current = bookings.filter(
            start__date__gt=today - timezone.timedelta(days=30),
        ).count()
        bookings_previous = bookings.filter(
            start__date__gt=today - timezone.timedelta(days=60),
            start__date__lte=today - timezone.timedelta(days=30),
        ).count()
        bookings_today = bookings.filter(
            start__date=today,
        ).count()
        cancelled_today = Appointment.objects.filter(
            status="Cancelled",
            start__date=today,
        ).count()
        completed_today = bookings.filter(
            status="Completed",
            start__date=today,
        ).count()
        no_show_today = Appointment.objects.filter(
            status="No show",
            start__date=today,
        ).count()
        recent_bookings = Appointment.objects.order_by("-start")[:30]
        today_schedule = Appointment.objects.filter(
            start__date=today,
        ).order_by("start")
        active_now = today_schedule.filter(
            status="In progress",
        ).order_by("start")

        return {
            "revenue_current": revenue_current,
            "revenue_previous": revenue_previous,
            "bookings_current": bookings_current,
            "bookings_previous": bookings_previous,
            "clients_current": clients_current,
            "clients_previous": clients_previous,
            "masters_current": masters_current,
            "masters_previous": masters_previous,
            "bookings_today": bookings_today,
            "completed_today": completed_today,
            "cancelled_today": cancelled_today,
            "no_show_today": no_show_today,
            "recent_bookings": [
                {
                    "id": recent_booking.id,
                    "client": recent_booking.client.get_full_name(),
                    "master": recent_booking.master.user.get_full_name(),
                    "service": recent_booking.service.name,
                    "date_time": recent_booking.start,
                    "status": recent_booking.status,
                    "price": recent_booking.service.price,
                }
                for recent_booking in recent_bookings
            ],
            "today_schedule": [
                {
                    "id": today_appointment.id,
                    "client": today_appointment.client.get_full_name(),
                    "master": today_appointment.master.user.get_full_name(),
                    "service": today_appointment.service.name,
                    "date_time": today_appointment.start,
                    "status": today_appointment.status,
                    "price": today_appointment.service.price,
                }
                for today_appointment in today_schedule
            ],
            "active_now": [
                {
                    "id": active_appointment.id,
                    "client": active_appointment.client.get_full_name(),
                    "master": active_appointment.master.user.get_full_name(),
                    "service": active_appointment.service.name,
                    "date_time": active_appointment.start,
                    "status": active_appointment.status,
                    "price": active_appointment.service.price,
                }
                for active_appointment in active_now
            ],
        }

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
