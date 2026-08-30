from typing import Any

from django.db.models import (
    Avg,
    Count,
    Q, QuerySet
)
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from users.models import MasterStatus

from .models import Salon, SalonStatus
from .permissions import IsAdminOrReadOnlyAll
from .serializers import (
    SalonListSerializer,
    SalonSerializer
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

    def get_ordering(self, request, queryset, view) -> list[Any]:
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
