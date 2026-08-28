from django.urls import path

from dashboard_statistics.views import MasterStatisticsView

app_name = "dashboard_statistics"

urlpatterns = [
    path(
        "masters/me/",
        MasterStatisticsView.as_view(),
        name="master-statistics",
    ),
]
