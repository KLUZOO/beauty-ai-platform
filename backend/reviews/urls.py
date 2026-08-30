from django.urls import path

from .views import (
    AppointmentReviewView,
    MasterReviewDetailView,
    MasterReviewListView,
    ReviewDetailView,
    ReviewListCreateView,
)

urlpatterns = [
    path("reviews/", ReviewListCreateView.as_view(), name="review-list-create"),
    path("reviews/<int:pk>/", ReviewDetailView.as_view(), name="review-detail"),
    path(
        "reviews/masters/me/", MasterReviewListView.as_view(), name="master-review-list"
    ),
    path(
        "reviews/<int:pk>/masters/me/",
        MasterReviewDetailView.as_view(),
        name="master-review-detail",
    ),
    path(
        "appointments/<int:appointment_id>/review/",
        AppointmentReviewView.as_view(),
        name="appointment-review",
    ),
]
