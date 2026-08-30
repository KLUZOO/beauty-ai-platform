from django.db.models import QuerySet
from django.utils import timezone

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from promotions.models import Promotion
from promotions.serializers import PromotionSerializer
from promotions.permissions import IsAdminOrReadOnlyAll

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="salon_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Filter promotions by salon ID.",
        ),
        OpenApiParameter(
            name="active",
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description=(
                    "Filter promotions by active status. "
                    "true - only active promotions, "
                    "false - only inactive promotions."
            ),
        ),
        OpenApiParameter(
            name="discount_percent",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Filter promotions by discount percentage (0-100).",
        ),
    ]
)
class PromotionViewSet(viewsets.ModelViewSet):
    serializer_class = PromotionSerializer
    permission_classes = (IsAdminOrReadOnlyAll,)

    def get_queryset(self) -> QuerySet:
        queryset = Promotion.objects.select_related("salon")

        salon_id = self.request.query_params.get("salon_id")
        active = self.request.query_params.get("active")
        discount_percent = self.request.query_params.get("discount_percent")

        if salon_id is not None:
            if not salon_id.isdigit():
                raise ValidationError(
                    {"salon_id": "Must be a positive integer."}
                )
            queryset = queryset.filter(salon_id=int(salon_id))

        if active is not None:
            active = active.lower()
            if active not in ("true", "false"):
                raise ValidationError(
                    {"active": "Must be 'true' or 'false'."}
                )

            now = timezone.now()

            if active == "true":
                queryset = queryset.filter(
                    start_date__lte=now,
                    end_date__gte=now,
                )
            else:
                queryset = queryset.exclude(
                    start_date__lte=now,
                    end_date__gte=now,
                )

        if discount_percent is not None:
            if not discount_percent.isdigit():
                raise ValidationError(
                    {"discount_percent": "Must be a positive integer."}
                )

            queryset = queryset.filter(
                discount_percent=int(discount_percent)
            )

        return queryset
