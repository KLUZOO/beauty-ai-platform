from celery import shared_task
from services.appointment_reminder_service import AppointmentReminderService
from services.email_service import EmailService


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
