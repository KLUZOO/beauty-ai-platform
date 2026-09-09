from django.urls import path

from dashboard_statistics.views import AdminStatisticsView, MasterStatisticsView

app_name = "dashboard_statistics"

urlpatterns = [
    path(
        "masters/me/",
        MasterStatisticsView.as_view(),
        name="master-statistics",
    ),
    path("admin/", AdminStatisticsView.as_view(), name="admin-statistics"),
]
