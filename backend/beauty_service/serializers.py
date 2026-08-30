from rest_framework import serializers
from salons.models import Salon
from users.models import Master

from .models import Service


class SalonServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salon
        fields = ("id", "name")


class MasterServicesSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")

    class Meta:
        model = Master
        fields = (
            "id",
            "first_name",
            "last_name",
            "average_rating",
        )


class ServicesSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    salons = SalonServiceSerializer(source="masters.salons", many=True, read_only=True)
    masters = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = (
            "id",
            "name",
            "description",
            "category",
            "price",
            "duration_minutes",
            "salons",
            "masters",
            "image",
        )

    def get_masters(self, service):
        available_master_ids_by_service = getattr(
            self.context["request"],
            "available_master_ids_by_service",
            None,
        )

        if available_master_ids_by_service is None:
            masters = service.masters.all()
        else:
            available_master_ids = available_master_ids_by_service.get(
                service.id,
                set(),
            )

            masters = service.masters.filter(
                id__in=available_master_ids,
            )

        return MasterServicesSerializer(
            masters,
            many=True,
        ).data
