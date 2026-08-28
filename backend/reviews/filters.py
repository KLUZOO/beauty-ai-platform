import django_filters

from .models import Review


class MasterReviewFilter(django_filters.FilterSet):
    rating = django_filters.NumberFilter()

    service = django_filters.CharFilter(
        field_name="appointment__service__name",
        lookup_expr="icontains",
    )

    date_from = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
    )

    date_to = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
    )

    class Meta:
        model = Review
        fields = (
            "rating",
            "service",
        )
