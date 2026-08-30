from django.utils.dateparse import parse_datetime
from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError

from beauty_service.services import AvailableMastersService

from .models import Service


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class ServicesFilter(filters.FilterSet):
    service_name = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
    )

    category = filters.CharFilter(
        field_name="category__name",
        lookup_expr="icontains",
    )

    salons = NumberInFilter(
        field_name="masters__salons__id",
    )

    masters = NumberInFilter(
        field_name="masters__id",
    )

    min_price = filters.NumberFilter(
        field_name="price",
        lookup_expr="gte",
    )

    max_price = filters.NumberFilter(
        field_name="price",
        lookup_expr="lte",
    )

    city = filters.CharFilter(
        field_name="masters__salons__city",
        lookup_expr="icontains",
    )

    class Meta:
        model = Service
        fields = ()

    available_datetime_from = filters.IsoDateTimeFilter(
        method="filter_available_datetime"
    )

    def filter_available_datetime(self, queryset, name, value):

        datetime_from = value

        datetime_to = parse_datetime(
            self.request.query_params.get("available_datetime_to")
        )

        if datetime_to is None:
            raise ValidationError(
                {"available_datetime_to": ["This query parameter is required."]}
            )

        if datetime_to <= datetime_from:
            raise ValidationError(
                {
                    "available_datetime_to": [
                        "Must be later than available_datetime_from."
                    ]
                }
            )

        available_service_ids = set()
        available_master_ids_by_service = {}

        master_ids = self.request.query_params.get("masters")
        salon_ids = self.request.query_params.get("salon")
        city = self.request.query_params.get("city")

        queryset = queryset.prefetch_related(
            "masters__salons",
        )

        for service in queryset:
            filtered_masters = service.masters.all()

            if master_ids:
                filtered_masters = filtered_masters.filter(id__in=master_ids.split(","))

            if salon_ids:
                filtered_masters = filtered_masters.filter(
                    salons__id__in=salon_ids.split(",")
                )

            if city:
                filtered_masters = filtered_masters.filter(salons__city__icontains=city)

            filtered_masters = filtered_masters.distinct()

            available_master_ids = (
                AvailableMastersService.get_ids_available_masters_by_service(
                    service=service,
                    masters=filtered_masters,
                    datetime_from=datetime_from,
                    datetime_to=datetime_to,
                )
            )

            if available_master_ids:
                available_service_ids.add(service.id)
                available_master_ids_by_service[service.id] = available_master_ids

        self.request.available_master_ids_by_service = available_master_ids_by_service

        return queryset.filter(id__in=available_service_ids)
