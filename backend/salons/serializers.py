from locations.models import Location
from rest_framework import serializers

from .models import Salon, SalonWorkingHours


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = (
            "id",
            "country",
            "city_name",
            "address",
            "region",
            "coordinates",
            "timezone",
            "city_tier",
        )
        read_only_fields = ("id",)


class SalonSerializer(serializers.ModelSerializer):
    location = LocationSerializer()

    class Meta:
        model = Salon
        fields = (
            "id",
            "name",
            "location",
            "phone",
            "opened_date",
            "owner",
            "masters",
            "description",
            "logo",
        )
        read_only_fields = (
            "id",
            "masters",
        )

    def create(self, validated_data):
        location_data = validated_data.pop("location")

        location, _ = Location.objects.get_or_create(
            country=location_data["country"],
            city_name=location_data["city_name"],
            address=location_data["address"],
            defaults=location_data,
        )

        return Salon.objects.create(
            location=location,
            **validated_data,
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
    location = LocationSerializer(read_only=True)

    class Meta:
        model = Salon
        fields = (
            "id",
            "name",
            "description",
            "logo",
            "location",
            "phone",
            "average_rating",
            "total_reviews",
            "masters_count",
            "service_count",
            "working_hours",
            "available_status",
        )
        read_only_fields = ("id",)
