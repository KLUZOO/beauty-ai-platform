from django.urls import path

from .views import (
    ClientAppointmentListView,
    RescheduleAppointmentView,
    CancelAppointmentView,
    AvailableSlotsView,
    MasterUpdateAppointmentStatusView,
    MasterAppointmentListView,
    MasterAppointmentDetailView,
    MasterAppointmentHistoryView,
    AvailableTimeSlotsView,
)

urlpatterns = [
    path(
        "my/", ClientAppointmentListView.as_view(), name="client-appointments-list"
    ),
    path(
        "<int:pk>/reschedule/", RescheduleAppointmentView.as_view(), name="appointment-reschedule"
    ),
    path(
        "<int:pk>/cancel/", CancelAppointmentView.as_view(), name="appointment-cancel"
    ),
    path(
        "available-slots/by-salon/", AvailableSlotsView.as_view(), name="available-slots-by-salon"
    ),
    path(
        "available-slots/by-master/", AvailableTimeSlotsView.as_view(), name="available-slots-by-master"
    ),
    path(
        "<int:pk>/status/", MasterUpdateAppointmentStatusView.as_view(), name="appointment-status-update"
    ),
    path(
        "master/active/", MasterAppointmentListView.as_view(), name="master-appointments-active"
    ),
    path(
        "master/history/", MasterAppointmentHistoryView.as_view(), name="master-appointments-history"
    ),
    path(
        "master/<int:pk>/", MasterAppointmentDetailView.as_view(), name="master-appointment-detail"
    ),
]
