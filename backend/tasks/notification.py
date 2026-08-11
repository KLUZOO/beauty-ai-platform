from celery import shared_task
from services.appointment_reminder_service import AppointmentReminderService
from services.email_service import EmailService
import logging


@shared_task
def send_email_task(
    recipient: str,
    subject: str,
    context: dict,
    template_name: str = "emails/notification.html",
    body: str | None = None,
) -> None:
    EmailService.send_email(
        recipient=recipient,
        subject=subject,
        context=context,
        template_name=template_name,
        body=body,
    )


@shared_task
def send_1h_reminders() -> None:
    AppointmentReminderService.send_1h_reminders()


@shared_task
def send_24h_reminders() -> None:
    AppointmentReminderService.send_24h_reminders()


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_appointment_event_task(self, payload: dict) -> None:
    """
    Celery task to handle appointment notification events (BE-BOOKING-07).
    """
    try:
        logger.info(
            f"Processing notification event '{payload.get('event_type')}' "
            f"for appointment {payload.get('appointment_id')}"
        )

        context = {
            "event_type": payload.get("event_type"),
            "appointment_id": payload.get("appointment_id"),
            "booking_date": payload.get("appointment_date"),
            "booking_time": payload.get("appointment_time"),
            "status": payload.get("appointment_status"),
        }

        logger.info(f"Notification payload processed successfully: {payload}")

    except Exception as exc:
        logger.error(f"Error publishing notification event for payload {payload}: {exc}")
        raise self.retry(exc=exc)
