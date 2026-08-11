from django.conf import settings

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator

from django.db import IntegrityError

from django.utils.encoding import (
    force_bytes,
    force_str
)
from django.utils.http import (
    urlsafe_base64_decode,
    urlsafe_base64_encode
)

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token as google_id_token

from rest_framework.exceptions import (
    AuthenticationFailed,
    ValidationError
)

from services.email_service import EmailService

User = get_user_model()


class UserRegistrationService:
    @staticmethod
    def register(validated_data) -> User:
        user = User.objects.create_user(
            **validated_data,
            is_active=False,
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verification_url = (
            f"https://extymandriy.github.io/verify_beauty_ai?token={token}&id={uid}"
        )

        EmailService.send_email(
            recipient=user.email,
            subject="Verify your email",
            context={
                "verification_url": verification_url,
            },
            template_name="emails/verification.html",
        )

        return user


class UserAuthService:
    @staticmethod
    def verify_email(uidb64: str, token: str) -> None:
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
        ):
            raise ValidationError("Invalid verification link.")

        if not default_token_generator.check_token(user, token):
            raise ValidationError("Invalid or expired token.")

        if user.is_active:
            return

        user.is_active = True
        user.save(update_fields=["is_active"])

    @staticmethod
    def authenticate_google_user(google_token: str | bytes) -> User:
        try:
            google_info = google_id_token.verify_oauth2_token(
                google_token,
                GoogleRequest(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as e:
            raise AuthenticationFailed("Invalid Google token.") from e

        if not google_info.get("email_verified"):
            raise AuthenticationFailed("Google email is not verified.")

        google_id = google_info.get("sub")
        email = google_info.get("email")
        first_name = google_info.get("given_name", "")
        last_name = google_info.get("family_name", "")

        if not email or not google_id:
            raise AuthenticationFailed("Invalid Google token.")

        user = User.objects.filter(google_id=google_id).first()

        if user is None:
            user = User.objects.filter(email=email).first()

        if user is None:
            user = User(
                google_id=google_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
            user.set_unusable_password()
            user.save()

        if not user.google_id:
            try:
                user.google_id = google_id
                user.save(update_fields=["google_id"])
            except IntegrityError as e:
                raise AuthenticationFailed(
                    "This Google account is already linked to another user."
                ) from e

        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

        return user
