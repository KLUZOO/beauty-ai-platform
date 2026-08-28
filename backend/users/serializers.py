from typing import (
    Any,
    ClassVar
)

from appointments.models import Appointment
from beauty_service.models import Service

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser

from django.core.exceptions import ValidationError as DjangoValidationError

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from salons.models import Salon

from users.models import (
    DayOff,
    Master,
    WorkingSchedule,
)

from users.services.auth_service import UserRegistrationService


User = get_user_model()


# USER MANAGEMENT SERIALIZERS
class UserSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating basic user data."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "is_staff",
            "is_active",
            "first_name",
            "last_name",
            "phone",
        )
        read_only_fields = ("is_staff", "is_active")
        extra_kwargs: ClassVar[dict[str, Any]] = {
            "password": {"write_only": True, "min_length": 5}
        }

    def create(self, validated_data: dict[str, Any]) -> Any:
        return UserRegistrationService.register(validated_data)

    # noinspection PyUnresolvedReferences
    def update(self, instance: Any, validated_data: dict[str, Any]) -> Any:
        """Update a user, securely set a new password if provided, and return it."""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for retrieving detailed user profile information (Read-Only)."""

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "phone",
            "email",
            "photo",
            "is_active",
            "is_staff",
            "birth_date",
            "date_joined",
            "is_master",
            "registration_date_user",
            "last_update_user",
        )
        read_only_fields = (
            "id",
            "is_active",
            "is_staff",
            "date_joined",
            "is_master",
            "registration_date_user",
            "last_update_user",
        )


# HELPER / NESTED SERIALIZERS
class AssignedSalonsSerializer(serializers.ModelSerializer):
    """Nested serializer for brief salon details."""

    class Meta:
        model = Salon
        fields = (
            "id",
            "name",
        )


class ServiceSerializer(serializers.ModelSerializer):
    """Nested serializer for services provided by a master."""

    class Meta:
        model = Service
        fields = (
            "id",
            "name",
        )


# MASTER SCHEDULE & DAY OFF SERIALIZERS
class WorkingScheduleSerializer(serializers.ModelSerializer):
    """Serializer for managing a master's working schedule by days of the week."""

    class Meta:
        model = WorkingSchedule
        fields = (
            "id",
            "weekday",
            "start_time",
            "end_time",
            "is_working_day",
        )
        read_only_fields = ("id",)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        instance = self.instance or WorkingSchedule()

        for attr, value in attrs.items():
            setattr(instance, attr, value)

        if instance.pk is None:
            instance.master = self.context["request"].user.master

        try:
            instance.clean()
        except DjangoValidationError as e:
            if hasattr(e, "message_dict"):
                raise serializers.ValidationError(e.message_dict)
            raise serializers.ValidationError(e.messages)

        return attrs

    def create(self, validated_data: dict[str, Any]) -> WorkingSchedule:
        if not validated_data["is_working_day"]:
            WorkingSchedule.objects.filter(
                master=validated_data["master"],
                weekday=validated_data["weekday"],
            ).delete()

        return super().create(validated_data)

    def update(
        self, instance: WorkingSchedule, validated_data: dict[str, Any]
    ) -> WorkingSchedule:
        if not validated_data.get("is_working_day", instance.is_working_day):
            WorkingSchedule.objects.filter(
                master=validated_data.get("master", instance.master),
                weekday=validated_data.get("weekday", instance.weekday),
            ).exclude(pk=instance.pk).delete()

        return super().update(instance, validated_data)


class DayOffSerializer(serializers.ModelSerializer):
    """Serializer for creating and validating a master's days off / vacations."""

    class Meta:
        model = DayOff
        fields = (
            "id",
            "start_date",
            "end_date",
            "reason",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    # noinspection PyUnresolvedReferences
    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        master = self.context["request"].user.master
        instance = self.instance

        start_date = attrs.get(
            "start_date",
            instance.start_date if instance else None,
        )
        end_date = attrs.get(
            "end_date",
            instance.end_date if instance else None,
        )

        if start_date is None or end_date is None:
            raise serializers.ValidationError("Start date and end date are required.")

        if start_date > end_date:
            raise serializers.ValidationError(
                "Start date cannot be greater than end date."
            )

        overlapping = DayOff.objects.filter(
            master=master,
            start_date__lte=end_date,
            end_date__gte=start_date,
        )

        if instance:
            overlapping = overlapping.exclude(pk=instance.pk)

        if overlapping.exists():
            raise serializers.ValidationError(
                "This period overlaps with another day off."
            )

        # Check for confirmed appointments falling within the day off period using start field
        appointments = Appointment.objects.filter(
            master=master,
            start__date__range=(start_date, end_date),
            status="confirmed",
        )

        if appointments.exists():
            raise serializers.ValidationError(
                "There are confirmed appointments within this period."
            )

        return attrs


# MASTER PROFILE SERIALIZERS
class MasterProfileSerializer(serializers.ModelSerializer):
    """Serializer for public and personal master profiles with nested relations."""

    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")
    phone = PhoneNumberField(source="user.phone")
    photo = serializers.ImageField(source="user.photo")
    assigned_salons = AssignedSalonsSerializer(
        source="salons",
        many=True,
        read_only=True,
    )
    active_services = ServiceSerializer(
        many=True,
        read_only=True,
    )
    working_schedule = WorkingScheduleSerializer(read_only=True, many=True)

    class Meta:
        model = Master
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "bio",
            "years_of_experience",
            "average_rating",
            "total_reviews",
            "assigned_salons",
            "active_services",
            "account_status",
            "registration_date_master",
            "last_update_master",
            "working_schedule",
            "photo",
        )
        read_only_fields = (
            "id",
            "registration_date_master",
            "last_update_master",
            "average_rating",
            "total_reviews",
            "account_status",
            "working_schedule",
        )

    def update(self, instance: Master, validated_data: dict[str, Any]) -> Master:
        user_data = validated_data.pop("user", {})

        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        return super().update(instance, validated_data)


class SalonShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salon
        fields = (
            "id",
            "name",
        )


class MasterListSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    photo = serializers.ImageField(source="user.photo")
    average_rating = serializers.FloatField(source="rating", read_only=True)
    salons = SalonShortSerializer(many=True, read_only=True)
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Master
        fields = (
            "id",
            "first_name",
            "last_name",
            "photo",
            "average_rating",
            "years_of_experience",
            "salons",
            "services",
        )
        read_only_fields = ("id",)


# AUTHENTICATION & PASSWORD MANAGEMENT
class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for handling password changes by authenticated users."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value: str) -> str:
        user: AbstractBaseUser = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect password.")

        return value

    def save(self, **kwargs: Any) -> AbstractBaseUser:
        user: AbstractBaseUser = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class SetPasswordSerializer(serializers.Serializer):
    """Serializer for setting a new password (e.g., after a password reset)."""

    new_password = serializers.CharField(write_only=True)

    def save(self, **kwargs: Any) -> AbstractBaseUser:
        user: AbstractBaseUser = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class GoogleLoginSerializer(serializers.Serializer):
    """Serializer for accepting Google ID tokens during OAuth2 authentication."""

    id_token = serializers.CharField()


class VerifyEmailSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
