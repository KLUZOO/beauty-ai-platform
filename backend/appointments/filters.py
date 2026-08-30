import django_filters

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
