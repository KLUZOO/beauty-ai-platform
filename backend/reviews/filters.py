import django_filters

from .models import Review


class MasterReviewFilter(django_filters.FilterSet):
    rating = django_filters.NumberFilter(
        field_name="rating",
        help_text="Filter by exact rating (1 to 5)",
    )

    service = django_filters.CharFilter(
        field_name="appointment__service__name",
        lookup_expr="icontains",
        help_text="Filter by service name (case-insensitive substring match)",
    )

    date_from = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
        help_text="Filter reviews created from this date (format: YYYY-MM-DD)",
    )

    date_to = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
        help_text="Filter reviews created up to this date (format: YYYY-MM-DD)",
    )

    class Meta:
        model = Review
        fields = ("rating", "service", "date_from", "date_to")


class ReviewFilter(django_filters.FilterSet):
    date_from = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    date_to = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
    )
    rating_from = django_filters.NumberFilter(
        field_name="rating",
        lookup_expr="gte",
    )
    rating_to = django_filters.NumberFilter(
        field_name="rating",
        lookup_expr="lte",
    )
    client = django_filters.NumberFilter(
        field_name="client_id",
    )
    master = django_filters.NumberFilter(
        field_name="appointment__master_id",
    )
    service = django_filters.NumberFilter(
        field_name="appointment__service_id",
    )

    class Meta:
        model = Review
        fields = [
            "date_from",
            "date_to",
            "rating_from",
            "rating_to",
            "client",
            "master",
            "service",
        ]
