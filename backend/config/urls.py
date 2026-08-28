"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.core.management import call_command
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.response import Response
from rest_framework.views import APIView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls", namespace="users")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/appointments/", include("appointments.urls")),
    path("api/salons/", include("salons.urls", namespace="salons")),
    path("api/", include("reviews.urls")),
    path("api/promotions/", include("promotions.urls", namespace="promotions")),
    path("api/payments/", include("payments.urls", namespace="payments")),
    path(
        "api/referral-events/",
        include("referral_events.urls", namespace="referral_events"),
    ),
    path(
        "api/dashboard-statistics/",
        include("dashboard_statistics.urls", namespace="dashboard_statistics"),
    ),
    path("api/services/", include("beauty_service.urls", namespace="services")),
]
if settings.APP_ENV == "development":

    class reset_db(APIView):
        def post(self, request, *args, **kwargs):
            call_command("flush", interactive=False)
            return Response({"message": "Database reset successfully."}, status=200)

    urlpatterns += [
        path("api/reset_db/", reset_db.as_view(), name="reset"),
    ]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
