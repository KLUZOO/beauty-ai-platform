from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class EmailService:
    @staticmethod
    def send_email(
        recipient: str,
        subject: str,
        context: dict,
        template_name: str = "emails/notification.html",
        body: str | None = None,
    ) -> None:
        html = render_to_string(template_name, context)

        message = EmailMultiAlternatives(
            subject=subject,
            body=body or "Your email client does not support HTML emails.",
            to=[recipient],
        )

        message.attach_alternative(html, "text/html")
        message.send()


if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    EmailService.send_email(
        recipient="example@gmail.com",
        subject="Test email",
        context={
            "customer_name": "Oleksandr",
            "appointment_status": "Confirmed",
            "salon_name": "Beauty Studio",
            "master_name": "Anna",
            "service_name": "Haircut",
            "appointment_date": "2026-07-23",
            "appointment_time": "15:30",
            "duration": "1 hour",
            "price": "500",
            "currency": "UAH",
            "notification_message": "Your appointment has been confirmed.",
        },
    )
