from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsMaster

from dashboard_statistics.serializers import (
    AdminAnalyticsSerializer,
    AdminDashboardSerializer,
    StatisticsSerializer,
)
from dashboard_statistics.services import StatisticsService


class MasterStatisticsView(APIView):
    permission_classes = (IsMaster,)

    # noinspection PyMethodMayBeStatic
    def get(self, request) -> Response:
        data = StatisticsService.get_master_statistics(master=request.user.master)
        serializer = StatisticsSerializer(data)
        return Response(serializer.data)


class AdminDashboardView(APIView):
    # permission_classes = (IsAdmin,)

    @extend_schema(
        summary="Get admin dashboard statistics",
        description="Returns statistics for the admin dashboard.",
        responses={200: AdminDashboardSerializer},
        tags=["Admin Statistics"],
    )
    def get(self, request) -> Response:
        data = StatisticsService.get_admin_dashboard(admin=request.user)
        serializer = AdminDashboardSerializer(data)
        return Response(serializer.data)


class AdminAnalyticsView(APIView):
    # permission_classes = (IsAdmin,)

    @extend_schema(
        summary="Get admin analytics",
        description="Returns analytics for the admin dashboard.",
        parameters=[
            OpenApiParameter(
                name="period",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                default=30,
                description="Analytics period in days. Must be greater than 0.",
            ),
        ],
        responses={200: AdminAnalyticsSerializer},
        tags=["Admin Statistics"],
    )
    def get(self, request) -> Response:
        try:
            period = int(request.query_params.get("period", "30"))
        except (ValueError, TypeError):
            return Response(
                {"detail": "Параметр period повинен бути цілим числом."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if period <= 0:
            return Response(
                {"detail": "Параметр period повинен бути більшим за 0."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = StatisticsService.get_admin_analytics(
            admin=request.user,
            period=period,
        )

        serializer = AdminAnalyticsSerializer(data)
        return Response(serializer.data)
