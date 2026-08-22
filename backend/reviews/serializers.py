from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    master = serializers.IntegerField(
        source="appointment.master.id",
        read_only=True,
    )
    client = serializers.IntegerField(
        source="appointment.client.id",
        read_only=True,
    )

    class Meta:
        model = Review
        fields = (
            "id",
            "appointment",
            "client",
            "master",
            "rating",
            "comment",
            "created_at",
        )
        read_only_fields = ("id", "client", "master", "created_at")


class MasterReviewSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(
        source="appointment.client.get_full_name",
        read_only=True,
    )

    client_profile_photo = serializers.ImageField(
        source="appointment.client.photo",
        read_only=True,
    )

    service_name = serializers.CharField(
        source="appointment.service.name",
        read_only=True,
    )

    appointment_date = serializers.DateField(
        source="appointment.start.date",
        read_only=True,
    )

    class Meta:
        model = Review
        fields = (
            "id",
            "client_name",
            "client_profile_photo",
            "rating",
            "comment",
            "service_name",
            "appointment_date",
            "created_at",
        )


class AppointmentReviewSerializer(serializers.ModelSerializer):
    master = serializers.IntegerField(source="appointment.master", read_only=True)
    client = serializers.IntegerField(source="appointment.client", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "appointment",
            "client",
            "master",
            "rating",
            "comment",
            "created_at",
        )
        read_only_fields = (
            "id",
            "appointment",
            "client",
            "master",
            "created_at",
        )
