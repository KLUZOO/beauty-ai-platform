from datetime import date as date_cls
from django.utils import timezone
from rest_framework import serializers

from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            "id",
            "client",
            "master",
            "salon",
            "service",
            "promo_id",
            "start",
            "end",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "client", "created_at"]

    def validate(self, attrs) -> dict:
        start = attrs.get("start")
        end = attrs.get("end")

        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end": "Час завершення має бути пізнішим за час початку."}
            )

        return super().validate(attrs)


class RescheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["start", "end"]

    def validate(self, attrs) -> dict:
        start = attrs.get("start", getattr(self.instance, "start", None))
        end = attrs.get("end", getattr(self.instance, "end", None))

        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end": "Час завершення має бути пізнішим за час початку."}
            )

        return super().validate(attrs)


class CancelSerializer(serializers.ModelSerializer):
    cancellation_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )

    class Meta:
        model = Appointment
        fields = ["cancellation_reason"]


class MasterStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["status", "cancellation_reason"]

    def validate(self, attrs) -> dict:
        status = attrs.get("status")
        cancellation_reason = attrs.get("cancellation_reason")

        if status == "cancelled" and not cancellation_reason:
            raise serializers.ValidationError(
                {"cancellation_reason": "Причина скасування обов'язкова при статусі 'cancelled'."}
            )

        return attrs


class MasterAppointmentListSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    service_name = serializers.CharField(source="service.name", read_only=True)
    duration_minutes = serializers.IntegerField(source="service.duration_minutes", read_only=True)
    total_price = serializers.DecimalField(source="service.price", max_digits=8, decimal_places=2, read_only=True)
    salon_name = serializers.CharField(source="salon.name", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "start",
            "end",
            "client_name",
            "service_name",
            "status",
            "duration_minutes",
            "total_price",
            "salon_name",
            "created_at",
        ]

    # noinspection PyMethodMayBeStatic
    def get_client_name(self, obj) -> str:
        return obj.client.get_full_name() or obj.client.email


class MasterAppointmentDetailSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(source="client.id", read_only=True)
    client_name = serializers.SerializerMethodField()
    client_phone = serializers.CharField(source="client.phone", read_only=True)
    client_email = serializers.EmailField(source="client.email", read_only=True)

    service_id = serializers.IntegerField(source="service.id", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    service_duration = serializers.IntegerField(source="service.duration_minutes", read_only=True)
    service_price = serializers.DecimalField(source="service.price", max_digits=8, decimal_places=2, read_only=True)

    salon_id = serializers.IntegerField(source="salon.id", read_only=True)
    salon_name = serializers.CharField(source="salon.name", read_only=True)
    salon_address = serializers.CharField(source="salon.address", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "start",
            "end",
            "status",
            "client_id",
            "client_name",
            "client_phone",
            "client_email",
            "service_id",
            "service_name",
            "service_duration",
            "service_price",
            "salon_id",
            "salon_name",
            "salon_address",
            "notes",
            "created_at",
            "updated_at",
        ]

    # noinspection PyMethodMayBeStatic
    def get_client_name(self, obj) -> str:
        return obj.client.get_full_name() or obj.client.email


class MasterAppointmentHistorySerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    service_name = serializers.CharField(source="service.name", read_only=True)
    duration_minutes = serializers.IntegerField(source="service.duration_minutes", read_only=True)
    total_price = serializers.DecimalField(source="service.price", max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "client_name",
            "service_name",
            "start",
            "end",
            "status",
            "total_price",
            "duration_minutes",
            "created_at",
            "completed_at",
            "cancellation_reason",
        ]

    # noinspection PyMethodMayBeStatic
    def get_client_name(self, obj) -> str:
        return obj.client.get_full_name() or obj.client.email


class AvailableSlotsQuerySerializer(serializers.Serializer):
    master_id = serializers.IntegerField(min_value=1)
    service_id = serializers.IntegerField(min_value=1)
    date = serializers.DateField()

    # noinspection PyMethodMayBeStatic
    def validate_date(self, value: date_cls) -> date_cls:
        """Не дозволяємо запитувати слоти на минулі дати."""
        if value < timezone.now().date():
            raise serializers.ValidationError("Date cannot be in the past.")
        return value


class AvailableSlotSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    availability_status = serializers.CharField()


class CreateAppointmentSerializer(serializers.Serializer):
    master_id = serializers.IntegerField(min_value=1)
    service_id = serializers.IntegerField(min_value=1)
    appointment_date = serializers.DateField()
    appointment_time = serializers.TimeField()
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)

    # noinspection PyMethodMayBeStatic
    def validate_appointment_date(self, value) -> str:
        if value < timezone.localdate():
            raise serializers.ValidationError("Неможливо створити запис на минулу дату.")
        return value


class AppointmentDetailSerializer(serializers.ModelSerializer):
    appointment_id = serializers.IntegerField(source="id", read_only=True)
    appointment_date = serializers.SerializerMethodField()
    appointment_time = serializers.SerializerMethodField()
    appointment_status = serializers.CharField(source="status", read_only=True)

    service_name = serializers.CharField(source="service.name", read_only=True)
    service_duration = serializers.IntegerField(source="service.duration_minutes", read_only=True)
    service_price = serializers.DecimalField(source="service.price", max_digits=8, decimal_places=2, read_only=True)

    salon_name = serializers.CharField(source="salon.name", read_only=True)
    salon_address = serializers.CharField(source="salon.address", read_only=True)

    master_id = serializers.SerializerMethodField()
    master_name = serializers.SerializerMethodField()

    client_id = serializers.IntegerField(source="client.id", read_only=True)
    client_name = serializers.SerializerMethodField()
    client_contact_information = serializers.SerializerMethodField()

    appointment_notes = serializers.ReadOnlyField(source="notes")
    created_date = serializers.DateTimeField(source="created_at", read_only=True)
    last_updated_date = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "appointment_id",
            "appointment_date",
            "appointment_time",
            "appointment_status",
            "service_name",
            "service_duration",
            "service_price",
            "salon_name",
            "salon_address",
            "master_id",
            "master_name",
            "client_id",
            "client_name",
            "client_contact_information",
            "appointment_notes",
            "created_date",
            "last_updated_date",
        ]

    # noinspection PyMethodMayBeStatic
    def get_appointment_date(self, obj) -> str:
        return obj.start.strftime("%Y-%m-%d") if obj.start else None

    # noinspection PyMethodMayBeStatic
    def get_appointment_time(self, obj) -> str:
        return obj.start.strftime("%H:%M") if obj.start else None

    # noinspection PyMethodMayBeStatic
    def get_master_id(self, obj) -> int:
        return obj.master.id if obj.master else None

    # noinspection PyMethodMayBeStatic
    def get_master_name(self, obj) -> str:
        if not obj.master:
            return None
        # Перевірка на наявність користувача або профілю
        user = getattr(obj.master, "user", obj.master)
        if hasattr(user, "get_full_name"):
            return user.get_full_name() or getattr(user, "email", str(user))
        return str(user)

    # noinspection PyMethodMayBeStatic
    def get_client_name(self, obj) -> str:
        if not obj.client:
            return None
        return obj.client.get_full_name() or obj.client.email

    # noinspection PyMethodMayBeStatic
    def get_client_contact_information(self, obj) -> dict:
        if not obj.client:
            return {}
        return {
            "email": getattr(obj.client, "email", None),
            "phone": getattr(obj.client, "phone", None),
        }


class AppointmentListSerializer(serializers.ModelSerializer):
    appointment_id = serializers.IntegerField(source="id", read_only=True)
    appointment_date = serializers.SerializerMethodField()
    appointment_time = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    master_name = serializers.SerializerMethodField()
    salon_name = serializers.CharField(source="salon.name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    appointment_status = serializers.CharField(source="status", read_only=True)
    total_price = serializers.DecimalField(
        source="service.price", max_digits=8, decimal_places=2, read_only=True
    )
    created_date = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "appointment_id",
            "appointment_date",
            "appointment_time",
            "client_name",
            "master_name",
            "salon_name",
            "service_name",
            "appointment_status",
            "total_price",
            "created_date",
        ]

    # noinspection PyMethodMayBeStatic
    def get_appointment_date(self, obj) -> str | None:
        return obj.start.strftime("%Y-%m-%d") if obj.start else None

    # noinspection PyMethodMayBeStatic
    def get_appointment_time(self, obj) -> str | None:
        return obj.start.strftime("%H:%M") if obj.start else None

    # noinspection PyMethodMayBeStatic
    def get_client_name(self, obj) -> str | None:
        if not obj.client:
            return None
        return obj.client.get_full_name() or obj.client.email

    # noinspection PyMethodMayBeStatic
    def get_master_name(self, obj) -> str | None:
        if not obj.master:
            return None
        user = getattr(obj.master, "user", obj.master)
        if hasattr(user, "get_full_name"):
            return user.get_full_name() or getattr(user, "email", str(user))
        return str(user)
