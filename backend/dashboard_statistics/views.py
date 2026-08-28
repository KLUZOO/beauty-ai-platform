from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsMaster

from dashboard_statistics.serializers import StatisticsSerializer
from dashboard_statistics.services import StatisticsService


class MasterStatisticsView(APIView):
    permission_classes = (IsMaster,)

    # noinspection PyMethodMayBeStatic
    def get(self, request) -> Response:
        data = StatisticsService.get_master_statistics(master=request.user.master)
        serializer = StatisticsSerializer(data)
        return Response(serializer.data)
