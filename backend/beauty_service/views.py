from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from users.models import MasterStatus

from beauty_service.filters import ServicesFilter

from .models import Service
from .serializers import ServicesSerializer


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
