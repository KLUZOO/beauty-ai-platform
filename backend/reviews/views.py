from appointments.models import Appointment
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, mixins, permissions, serializers
from rest_framework.filters import OrderingFilter
from users.permissions import IsMaster

from reviews.filters import MasterReviewFilter

from .models import Review
from .serializers import (
    AppointmentReviewSerializer,
    MasterReviewSerializer,
    ReviewSerializer,
)


@extend_schema_view(
    get=extend_schema(
        summary="List all reviews",
        responses={200: ReviewSerializer(many=True)},
    ),
    post=extend_schema(
        summary="Create a review",
        responses={
            201: ReviewSerializer,
            400: OpenApiResponse(
                description="Validation error (e.g., trying to review someone else's or uncompleted appointment)"
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
        },
    ),
)
class ReviewListCreateView(generics.ListCreateAPIView):
    """
    GET /api/reviews/ — list of all reviews, available to anyone (even without authorization)
    POST /api/reviews/ — leave a review for your completed booking, authorization required

    Request body for POST: {"appointment": 5, "rating": 4, "comment": "..."}
    client and master are determined automatically from appointment, they do not need to be passed.
    """

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self) -> list:
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer) -> None:
        appointment = serializer.validated_data.get("appointment")

        if appointment.client_id != self.request.user.id:
            raise serializers.ValidationError(
                "Можна залишити відгук тільки на власне бронювання."
            )

        if appointment.status != "completed":
            raise serializers.ValidationError(
                "Відгук можна залишити тільки на завершене бронювання."
            )

        serializer.save(client=self.request.user)


@extend_schema(
    summary="Retrieve a review",
    responses={
        200: ReviewSerializer,
        404: OpenApiResponse(description="Review not found"),
    },
)
class ReviewDetailView(generics.RetrieveAPIView):
    """
    GET /api/reviews/<id>/ — details of one review, available to anyone.
    Editing and deleting reviews is not yet provided.
    """

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]


class MasterReviewQuerysetMixin:
    def get_queryset(self) -> QuerySet[Review]:
        return Review.objects.filter(
            appointment__master=self.request.user.master,
            appointment__status="completed",
        ).select_related(
            "appointment",
            "appointment__client",
            "appointment__service",
        )


@extend_schema(
    summary="List reviews for current master",
    description="Retrieve all reviews left for completed appointments of the authenticated master.",
    parameters=[
        OpenApiParameter(
            name="rating",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="Filter by exact rating (1 to 5)",
        ),
        OpenApiParameter(
            name="service",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by service name (case-insensitive search)",
        ),
        OpenApiParameter(
            name="date_from",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description="Filter reviews created from this date (YYYY-MM-DD)",
        ),
        OpenApiParameter(
            name="date_to",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description="Filter reviews created up to this date (YYYY-MM-DD)",
        ),
    ],
    responses={
        200: MasterReviewSerializer(many=True),
        401: OpenApiResponse(
            description="Authentication credentials were not provided"
        ),
        403: OpenApiResponse(description="Permission denied (Requires master profile)"),
    },
)
class MasterReviewListView(MasterReviewQuerysetMixin, generics.ListAPIView):
    serializer_class = MasterReviewSerializer
    permission_classes = (IsMaster,)
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    filterset_class = MasterReviewFilter
    ordering_fields = (
        "created_at",
        "rating",
    )
    ordering = ("-created_at",)


@extend_schema(
    summary="Retrieve a specific review for current master",
    responses={
        200: MasterReviewSerializer,
        401: OpenApiResponse(
            description="Authentication credentials were not provided"
        ),
        403: OpenApiResponse(description="Permission denied"),
        404: OpenApiResponse(
            description="Review not found or does not belong to this master"
        ),
    },
)
class MasterReviewDetailView(MasterReviewQuerysetMixin, generics.RetrieveAPIView):
    serializer_class = MasterReviewSerializer
    permission_classes = (IsMaster,)


@extend_schema_view(
    get=extend_schema(
        summary="Get review for specific appointment",
        responses={
            200: AppointmentReviewSerializer,
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            404: OpenApiResponse(description="Review not found"),
        },
    ),
    post=extend_schema(
        summary="Create review for specific appointment",
        responses={
            201: AppointmentReviewSerializer,
            400: OpenApiResponse(
                description="Validation error (e.g., review already exists, appointment is not completed, or not owned by user)"
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            404: OpenApiResponse(description="Appointment not found"),
        },
    ),
    patch=extend_schema(
        summary="Update review for specific appointment",
        responses={
            200: AppointmentReviewSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            404: OpenApiResponse(description="Review not found"),
        },
    ),
    delete=extend_schema(
        summary="Delete review for specific appointment",
        responses={
            204: OpenApiResponse(description="Review successfully deleted"),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            404: OpenApiResponse(description="Review not found"),
        },
    ),
)
class AppointmentReviewView(
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    serializer_class = AppointmentReviewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return get_object_or_404(
            Review,
            appointment_id=self.kwargs["appointment_id"],
        )

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def check_appointment(self, appointment):
        if appointment.client != self.request.user:
            raise serializers.ValidationError("You cannot review this appointment.")

        if appointment.status != "completed":
            raise serializers.ValidationError("The appointment must be completed.")

    def perform_create(self, serializer):
        appointment = get_object_or_404(
            Appointment,
            id=self.kwargs["appointment_id"],
        )

        self.check_appointment(appointment)

        if Review.objects.filter(appointment=appointment).exists():
            raise serializers.ValidationError("Review already exists.")

        serializer.save(appointment=appointment)

    def perform_update(self, serializer):
        self.check_appointment(
            self.get_object().appointment,
        )
        serializer.save()

    def perform_destroy(self, instance):
        self.check_appointment(instance.appointment)
        instance.delete()
