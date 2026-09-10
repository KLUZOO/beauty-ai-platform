from drf_spectacular.utils import extend_schema
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
    permission_classes = (IsMaster,)

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
    permission_classes = (IsMaster,)

    @extend_schema(
        summary="Get admin analytics",
        description="Returns analytics for the admin dashboard.",
        responses={200: AdminAnalyticsSerializer},
        tags=["Admin Statistics"],
    )
    def get(self, request) -> Response:
        data = StatisticsService.get_admin_analytics(admin=request.user)
        serializer = AdminAnalyticsSerializer(data)
        return Response(serializer.data)
