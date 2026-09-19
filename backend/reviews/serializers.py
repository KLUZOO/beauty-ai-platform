from beauty_service.models import Service
from rest_framework import serializers
from users.models import User

from .models import Review


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "photo",
        )


class ServiceSerializers(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = (
            "id",
            "category",
            "name",
            "image",
        )


class ReviewSerializer(serializers.ModelSerializer):
    master = serializers.IntegerField(
        source="appointment.master.id",
        read_only=True,
    )
    client = ClientSerializer(read_only=True)
    service = ServiceSerializers(
        source="appointment.service",
        read_only=True,
    )

    class Meta:
        model = Review
        fields = (
            "id",
            "appointment",
            "service",
            "client",
            "master",
            "rating",
            "comment",
            "created_at",
        )
        read_only_fields = ("id", "client", "master", "created_at")


class MasterReviewSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    appointment_date = serializers.SerializerMethodField()

    client_profile_photo = serializers.ImageField(
        source="appointment.client.photo",
        read_only=True,
    )

    service_name = serializers.CharField(
        source="appointment.service.name",
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

    def get_client_name(self, obj):
        return obj.appointment.client.get_full_name()

    def get_appointment_date(self, obj):
        return obj.appointment.start.date()


class MasterReviewsResponseSerializer(serializers.Serializer):
    reviews = MasterReviewSerializer(many=True)
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()


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
