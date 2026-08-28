from django.urls import path

from .views import (
    SalonDetailView,
    SalonListCreateView,
    SalonListView
)

app_name = "salons"

urlpatterns = [
    path("create-list/", SalonListCreateView.as_view(), name="salon-list-create"),
    path("<int:pk>/", SalonDetailView.as_view(), name="salon-detail"),
    path("", SalonListView.as_view(), name="salon-list"),
]
