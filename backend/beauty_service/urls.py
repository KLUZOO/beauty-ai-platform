from django.urls import path

from .views import ServicesListView

app_name = "services"

urlpatterns = [
    path("", ServicesListView.as_view(), name="list"),
]
