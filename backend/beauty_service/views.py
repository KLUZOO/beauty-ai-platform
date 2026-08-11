from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from users.models import MasterStatus

from beauty_service.filters import ServicesFilter

from .models import Service
from .serializers import ServicesSerializer


@extend_schema(
    summary="List active services",
    description=(
        "Retrieve a list of active beauty services. Supports filtering by name, category, salon, "
        "master, price range, city, and datetime availability window."
    ),
    parameters=[
        OpenApiParameter(
            name="service_name",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by service name (case-insensitive search)",
        ),
        OpenApiParameter(
            name="category",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by category name (case-insensitive search)",
        ),
        OpenApiParameter(
            name="salons",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by salon ID or comma-separated list of IDs (e.g. `1` or `1,2,3`)",
        ),
        OpenApiParameter(
            name="masters",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by master ID or comma-separated list of IDs (e.g. `5` or `5,10`)",
        ),
        OpenApiParameter(
            name="min_price",
            type=OpenApiTypes.NUMBER,
            location=OpenApiParameter.QUERY,
            description="Filter by minimum price (greater than or equal)",
        ),
        OpenApiParameter(
            name="max_price",
            type=OpenApiTypes.NUMBER,
            location=OpenApiParameter.QUERY,
            description="Filter by maximum price (less than or equal)",
        ),
        OpenApiParameter(
            name="city",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by salon city (case-insensitive search)",
        ),
        OpenApiParameter(
            name="available_datetime_from",
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            description="Start of datetime window for availability check (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ). **Requires `available_datetime_to`**.",
        ),
        OpenApiParameter(
            name="available_datetime_to",
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            description="End of datetime window for availability check (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ). **Must be later than `available_datetime_from`**.",
        ),
        OpenApiParameter(
            name="ordering",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Which field to use when ordering the results. Options: `name`, `popularity`, `price`, `duration_minutes`. Prefix with `-` for descending order.",
            enum=[
                "name",
                "-name",
                "popularity",
                "-popularity",
                "price",
                "-price",
                "duration_minutes",
                "-duration_minutes",
            ],
        ),
    ],
    responses={
        200: ServicesSerializer(many=True),
        400: OpenApiResponse(
            description=(
                "Validation error (e.g. `available_datetime_from` was passed without "
                "`available_datetime_to`, or `available_datetime_to` is earlier than `available_datetime_from`)"
            )
        ),
    },
)
class ServicesListView(generics.ListAPIView):
    serializer_class = ServicesSerializer
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    filterset_class = ServicesFilter

    ordering_fields = (
        "name",
        "popularity",
        "price",
        "duration_minutes",
    )

    def get_queryset(self):
        return (
            Service.objects.filter(
                is_active=True, masters__account_status=MasterStatus.ACTIVE
            )
            .annotate(
                popularity=Count(
                    "masters__appointments",
                    filter=Q(masters__appointments__status="completed"),
                    distinct=True,
                )
            )
            .distinct()
        )
