from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters import rest_framework as filters


class UsersFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_name")

    birth_date_from = filters.DateFilter(
        field_name="birth_date",
        lookup_expr="gte",
    )

    birth_date_to = filters.DateFilter(
        field_name="birth_date",
        lookup_expr="lte",
    )

    gender = filters.CharFilter(
        field_name="gender",
        lookup_expr="exact",
    )

    def filter_name(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value) | Q(last_name__icontains=value)
        )

    class Meta:
        model = get_user_model()
        fields = ()
