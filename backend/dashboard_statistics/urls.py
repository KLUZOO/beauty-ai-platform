from django.urls import path

from dashboard_statistics.views import (
    AdminAnalyticsView,
    AdminDashboardView,
    MasterStatisticsView,
)

app_name = "dashboard_statistics"

urlpatterns = [
    path(
        "masters/me/",
        MasterStatisticsView.as_view(),
        name="master-statistics",
    ),
    path("dashboard/", AdminDashboardView.as_view(), name="admin-statistics"),
    path("analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
]
