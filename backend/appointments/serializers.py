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
    class Meta:
        model = Appointment
        fields = []


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
