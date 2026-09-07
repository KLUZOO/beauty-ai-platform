import django_filters

from .models import Salon


class SalonFilter(django_filters.FilterSet):
    # alias: the client (including the AI assistant) simply passes "city",
    # but in fact we filter by the nested field location.city_name
    city = django_filters.CharFilter(
        field_name="location__city_name",
        lookup_expr="icontains",
    )
    name = django_filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
    )

    class Meta:
        model = Salon
        fields = ["city", "name"]
