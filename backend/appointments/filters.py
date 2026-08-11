import django_filters
from django.db.models import (
    Q,
    QuerySet
)

from .models import Appointment


class MasterAppointmentFilter(django_filters.FilterSet):
    # lookup_expr="date": Extracts only the YYYY-MM-DD part from the 'start' DateTimeField
    # and checks for an exact match (SQL: WHERE DATE(start) = 'YYYY-MM-DD')
    appointment_date = django_filters.DateFilter(
        field_name="start", lookup_expr="date"
    )
    status = django_filters.CharFilter()

    # lookup_expr="icontains": Case-insensitive partial match search on client email
    # (SQL: WHERE client.email ILIKE '%query%')
    client = django_filters.CharFilter(
        field_name="client__email",
        lookup_expr="icontains",
    )

    # lookup_expr="icontains": Case-insensitive partial match search on service name
    # (SQL: WHERE service.name ILIKE '%query%')
    service = django_filters.CharFilter(
        field_name="service__name",
        lookup_expr="icontains",
    )

    class Meta:
        model = Appointment
        fields = ["appointment_date", "status", "client", "service"]


class MasterAppointmentHistoryFilter(django_filters.FilterSet):
    # lookup_expr="date__gte": Extracts date from 'start' and checks if it is Greater Than or Equal to date_from
    # (SQL: WHERE DATE(start) >= 'YYYY-MM-DD')
    date_from = django_filters.DateFilter(
        field_name="start", lookup_expr="date__gte"
    )

    # lookup_expr="date__lte": Extracts date from 'start' and checks if it is Less Than or Equal to date_to
    # (SQL: WHERE DATE(start) <= 'YYYY-MM-DD')
    date_to = django_filters.DateFilter(
        field_name="start", lookup_expr="date__lte"
    )
    status = django_filters.CharFilter()
    client = django_filters.CharFilter(
        field_name="client__email",
        lookup_expr="icontains",
    )
    service = django_filters.CharFilter(
        field_name="service__name",
        lookup_expr="icontains",
    )

    class Meta:
        model = Appointment
        fields = ["date_from", "date_to", "status", "client", "service"]


class AppointmentListFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(field_name="start", lookup_expr="date")
    date_from = django_filters.DateFilter(field_name="start", lookup_expr="date__gte")
    date_to = django_filters.DateFilter(field_name="start", lookup_expr="date__lte")

    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    salon = django_filters.CharFilter(field_name="salon__name", lookup_expr="icontains")
    master = django_filters.CharFilter(method="filter_by_master")
    service = django_filters.CharFilter(field_name="service__name", lookup_expr="icontains")
    client = django_filters.CharFilter(method="filter_by_client")

    class Meta:
        model = Appointment
        fields = ["date", "date_from", "date_to", "status", "salon", "master", "service", "client"]

    # noinspection PyMethodMayBeStatic
    def filter_by_master(self, queryset, _name, value) -> QuerySet:
        return queryset.filter(
            Q(master__user__first_name__icontains=value) |
            Q(master__user__last_name__icontains=value) |
            Q(master__user__email__icontains=value)
        )

    # noinspection PyMethodMayBeStatic
    def filter_by_client(self, queryset, _name, value) -> QuerySet:
        return queryset.filter(
            Q(client__first_name__icontains=value) |
            Q(client__last_name__icontains=value) |
            Q(client__email__icontains=value)
        )
