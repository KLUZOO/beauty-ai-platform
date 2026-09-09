from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsMaster

from dashboard_statistics.permissions import IsAdmin
from dashboard_statistics.serializers import (
    AdminStatisticsSerializer,
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


class AdminStatisticsView(APIView):
    permission_classes = (IsAdmin,)

    @extend_schema(
        summary="Get admin statistics",
        description="Returns statistics for the admin dashboard.",
        responses={200: AdminStatisticsSerializer},
        tags=["Admin Statistics"],
    )
    def get(self, request) -> Response:
        data = StatisticsService.get_admin_statistics(admin=request.user)
        serializer = AdminStatisticsSerializer(data)
        return Response(serializer.data)
