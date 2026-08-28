from rest_framework import serializers

from .models import (
    Salon,
    SalonWorkingHours
)


class SalonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salon
        fields = (
            "id",
            "name",
            "city",
            "district",
            "address",
            "phone",
            "opened_date",
            "latitude",
            "longitude",
            "owner",
            "masters",
            "description",
            "logo",
        )
        read_only_fields = (
            "id",
            "masters",
        )


class WorkingScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalonWorkingHours
        fields = (
            "weekday",
            "opening_time",
            "closing_time",
            "is_closed",
        )


class SalonListSerializer(serializers.ModelSerializer):
    working_hours = WorkingScheduleSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_reviews = serializers.IntegerField(read_only=True)
    masters_count = serializers.IntegerField(read_only=True)
    service_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Salon
        fields = (
            "id",
            "name",
            "description",
            "logo",
            "address",
            "city",
            "phone",
            "average_rating",
            "total_reviews",
            "masters_count",
            "service_count",
            "working_hours",
            "available_status",
        )
        read_only_fields = ("id",)
