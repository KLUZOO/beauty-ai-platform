from django.db.models import QuerySet
from rest_framework import serializers


class StrictFilterOrderingMixin:
    """
    A mixin for generic views that adds strict validation of query parameters
    for filtering and sorting — returns 400 Bad Request instead of
    silently ignoring invalid values.

    A class using this mixin must define:
    - filterset_class
    - ordering_fields
    """

    def filter_queryset(self, queryset) -> QuerySet:
        # Validate filter parameters explicitly to return HTTP 400 Bad Request on invalid input
        filterset = self.filterset_class(self.request.query_params, queryset=queryset)
        if not filterset.is_valid():
            raise serializers.ValidationError(filterset.errors)
        queryset = filterset.qs

        # Validate ordering query param against allowed fields
        ordering_param = self.request.query_params.get("ordering")
        if ordering_param:
            requested_fields = [f.lstrip("-") for f in ordering_param.split(",")]
            invalid_fields = [
                f for f in requested_fields if f not in self.ordering_fields
            ]
            if invalid_fields:
                raise serializers.ValidationError(
                    {
                        "ordering": "Недопустимі поля сортування: %s"
                                    % ", ".join(invalid_fields)
                    }
                )

        return super().filter_queryset(queryset)
