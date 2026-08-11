from typing import Sequence

from django.db.models import (
    Avg,
    Count,
    Q,
    QuerySet
)
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from users.models import MasterStatus

from .models import Salon, SalonStatus
from .permissions import IsAdminOrReadOnlyAll
from .serializers import SalonListSerializer, SalonSerializer


@extend_schema_view(
    get=extend_schema(
        summary="List all basic salons",
        description="Retrieve a list of all raw salon entities. Accessible to unauthenticated users.",
        responses={200: SalonSerializer(many=True)},
    ),
    post=extend_schema(
        summary="Create a new salon",
        description="Create a new salon entry. Restricted to staff/admin users.",
        request=SalonSerializer,
        responses={
            201: SalonSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            403: OpenApiResponse(
                description="Permission denied (Requires staff access)"
            ),
        },
    ),
)
class SalonListCreateView(generics.ListCreateAPIView):
    """
    GET /api/salons/ — list of all salons, accessible to anyone (even without authorization)
    POST /api/salons/ — create a new salon, only for admins (is_staff)

    TODO: when the master verification system is ready (Master.is_verified) —
    perhaps allow also verified masters, not only is_staff
    """

    queryset = Salon.objects.prefetch_related("masters")
    serializer_class = SalonSerializer
    permission_classes = [IsAdminOrReadOnlyAll]

@extend_schema_view(
    get=extend_schema(
        summary="Retrieve a salon",
        description="Get detailed raw information about a specific salon by ID.",
        responses={
            200: SalonSerializer,
            404: OpenApiResponse(description="Salon not found"),
        },
    ),
    put=extend_schema(
        summary="Update a salon (full)",
        description="Update all fields of an existing salon. Restricted to staff users.",
        request=SalonSerializer,
        responses={
            200: SalonSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Salon not found"),
        },
    ),
    patch=extend_schema(
        summary="Update a salon (partial)",
        description="Partially update specific fields of a salon. Restricted to staff users.",
        request=SalonSerializer,
        responses={
            200: SalonSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Salon not found"),
        },
    ),
    delete=extend_schema(
        summary="Delete a salon",
        description="Permanently remove a salon record. Restricted to staff users.",
        responses={
            204: OpenApiResponse(description="Salon successfully deleted"),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Salon not found"),
        },
    ),
)
class SalonDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/salons/<id>/ — details of one salon, accessible to anyone
    PATCH /api/salons/<id>/ — editing, only for admins (is_staff)
    DELETE /api/salons/<id>/ — deletion, only for admins (is_staff)
    """

    queryset = Salon.objects.prefetch_related("masters")
    serializer_class = SalonSerializer
    permission_classes = [IsAdminOrReadOnlyAll]


class SalonOrderingFilter(OrderingFilter):
    ORDERING_MAP = {
        "rating": "average_rating",
        "name": "name",
        "reviews": "total_reviews",
        "popularity": "completed_services",
    }

    def get_ordering(self, request, queryset, view) -> Sequence[str] | None:
        ordering = super().get_ordering(request, queryset, view)

        if not ordering:
            return ordering

        result = []

        for field in ordering:
            desc = field.startswith("-")
            key = field.lstrip("-")

            mapped = self.ORDERING_MAP.get(key, key)

            if key == "popularity":
                if desc:
                    result.extend(
                        [
                            "-completed_services",
                            "-average_rating",
                        ]
                    )
                else:
                    result.extend(
                        [
                            "completed_services",
                            "average_rating",
                        ]
                    )
            else:
                result.append(f"-{mapped}" if desc else mapped)

        return result

@extend_schema(
    summary="List active salons with details and metrics",
    description=(
        "Retrieves active salons containing active masters with at least one active service. "
        "Includes calculated aggregations such as average ratings, review counts, active master count, "
        "and working schedules."
    ),
    parameters=[
        OpenApiParameter(
            name="ordering",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description=(
                "Which field to use when ordering the results. Options: "
                "`rating`, `reviews`, `popularity`, `name`. "
                "Prefix with `-` for descending order (e.g., `-rating`). Default is `-rating`."
            ),
            enum=[
                "rating",
                "-rating",
                "reviews",
                "-reviews",
                "popularity",
                "-popularity",
                "name",
                "-name",
            ],
        ),
    ],
    responses={200: SalonListSerializer(many=True)},
)
class SalonListView(generics.ListAPIView):
    serializer_class = SalonListSerializer
    filter_backends = (SalonOrderingFilter,)

    ordering_fields = {
        "rating": "average_rating",
        "reviews": "total_reviews",
        "popularity": "completed_services",
        "name": "name",
    }

    ordering = ("-average_rating",)

    def get_queryset(self) -> QuerySet[Salon, Salon]:
        return (
            Salon.objects.filter(
                masters__account_status=MasterStatus.ACTIVE,
                salon_status=SalonStatus.ACTIVE,
            )
            .annotate(
                average_rating=Avg("appointments__review__rating"),
                total_reviews=Count("appointments__review", distinct=True),
                masters_count=Count("masters", distinct=True),
                service_count=Count(
                    "masters__services",
                    filter=Q(masters__services__is_active=True),
                    distinct=True,
                ),
                completed_services=Count(
                    "appointments",
                    filter=Q(appointments__status="completed"),
                    distinct=True,
                ),
            )
            .filter(service_count__gt=0)
            .prefetch_related("working_hours")
            .distinct()
        )
