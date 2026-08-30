from datetime import (
    datetime,
    timedelta
)

from django.db.models import QuerySet
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    filters,
    generics,
    serializers
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from rest_framework import status as http_status

from users.permissions import IsMaster
from .models import Appointment
from .serializers import (
    AppointmentSerializer,
    RescheduleSerializer,
    CancelSerializer,
    MasterStatusUpdateSerializer,
    MasterAppointmentListSerializer,
    MasterAppointmentDetailSerializer,
    MasterAppointmentHistorySerializer
)
from .filters import (
    MasterAppointmentFilter,
    MasterAppointmentHistoryFilter
)

from beauty_service.models import Service
from salons.models import Salon

from tasks.notification import send_email_task


class ClientAppointmentListView(generics.ListAPIView):
    """
    GET /api/appointments/my/

    List of reservations for the currently authenticated client.
    Supports:
      - filter by status:  ?status=confirmed
      - sort:         ?ordering=start  (or -start)
      - pagination:   ?page=2
    """

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status"]
    # Updated ordering fields to reflect the model's new 'start' field
    ordering_fields = ["start", "created_at"]
    ordering = ["-start"]  # Default sorting: newest first

    def get_queryset(self) -> QuerySet[Appointment]:
        # Filter appointments to display only those belonging to the logged-in client
        return Appointment.objects.filter(client=self.request.user)


class RescheduleAppointmentView(generics.UpdateAPIView):
    """
    PATCH /api/appointments/<id>/reschedule/

    Moves an existing customer reservation to a new datetime interval.
    Request body: {"start": "2026-08-01T14:00:00Z", "end": "2026-08-01T15:00:00Z"}
    """

    serializer_class = RescheduleSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["patch"]

    def get_queryset(self) -> QuerySet[Appointment]:
        # Restrict rescheduling strictly to the user's own appointments
        return Appointment.objects.filter(client=self.request.user)

    def perform_update(self, serializer) -> None:
        # Prevent rescheduling if the appointment is already completed or canceled
        appointment = self.get_object()
        if appointment.status in ["cancelled", "completed"]:
            raise serializers.ValidationError(
                "Неможливо перенести бронювання зі статусом '%s'." % appointment.status
            )
        serializer.save(status="pending")


class CancelAppointmentView(generics.UpdateAPIView):
    """
    PATCH /api/appointments/<id>/cancel/

    Cancels the customer's upcoming booking (sets the status to "canceled").
    The request body is optional.
    """

    serializer_class = CancelSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["patch"]

    def get_queryset(self) -> QuerySet[Appointment]:
        # Restrict cancellation strictly to the user's own appointments
        return Appointment.objects.filter(client=self.request.user)

    def perform_update(self, serializer) -> None:
        # Prevent cancellation for past or already canceled appointments
        appointment = self.get_object()
        if appointment.status in ["cancelled", "completed"]:
            raise serializers.ValidationError(
                "Бронювання зі статусом '%s' вже неможливо скасувати."
                % appointment.status
            )
        serializer.save(status="cancelled")


class AvailableSlotsView(APIView):
    """
    GET /api/appointments/available-slots/?salon=1&master=3&service=5&date_from=2026-08-01&date_to=2026-08-03

    Returns a list of available time slots for booking, grouped by date.
    Required query params:
      - salon     — salon id (to fetch daily working hours)
      - master    — master id (to query busy time ranges)
      - service   — service id (to compute required slot duration)
      - date_from — start date, format YYYY-MM-DD
      - date_to   — end date, format YYYY-MM-DD (inclusive; defaults to date_from)

    Response:
      {
        "2026-08-01": [{"start": "10:00", "end": "10:45"}, ...],
        "2026-08-02": []   ← empty list if closed or fully booked
      }
    """

    permission_classes = [IsAuthenticated]

    # noinspection PyMethodMayBeStatic
    def get(self, request) -> Response:
        salon_id = request.query_params.get("salon")
        master_id = request.query_params.get("master")
        service_id = request.query_params.get("service")
        date_from_str = request.query_params.get("date_from")
        date_to_str = request.query_params.get("date_to") or date_from_str

        if not all([salon_id, master_id, service_id, date_from_str]):
            raise serializers.ValidationError(
                "Потрібно передати параметри: salon, master, service, date_from."
            )

        try:
            date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
            date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()
        except ValueError:
            raise serializers.ValidationError(
                "Невірний формат дати, очікується YYYY-MM-DD."
            )

        if date_to < date_from:
            raise serializers.ValidationError("date_to не може бути раніше date_from.")

        try:
            salon = Salon.objects.get(pk=salon_id)
        except Salon.DoesNotExist:
            raise serializers.ValidationError("Салон з таким id не знайдено.")

        try:
            service = Service.objects.get(pk=service_id)
        except Service.DoesNotExist:
            raise serializers.ValidationError("Послугу з таким id не знайдено.")

        duration = timedelta(minutes=service.duration_minutes)
        step = timedelta(minutes=15)

        # Preload salon opening hours mapped by weekday integer (0=Monday, 6=Sunday)
        # noinspection PyUnresolvedReferences
        working_hours_by_weekday = {wh.weekday: wh for wh in salon.working_hours.all()}

        result = {}
        current_date = date_from

        while current_date <= date_to:
            weekday = current_date.weekday()
            schedule = working_hours_by_weekday.get(weekday)

            # Skip calculation if the salon has no schedule or is marked closed for this weekday
            # noinspection PyUnresolvedReferences
            if schedule is None or schedule.is_closed:
                result[current_date.isoformat()] = []
                current_date += timedelta(days=1)
                continue

            # Fetch existing non-canceled appointments for the target master on this date
            busy_appointments = (
                Appointment.objects.filter(
                    master_id=master_id,
                    start__date=current_date,
                )
                .exclude(status="cancelled")
                .order_by("start")
            )

            # Build list of occupied (start_datetime, end_datetime) tuples
            busy_intervals = [
                (a.start, a.end)
                for a in busy_appointments
            ]

            # Construct datetime boundaries for the master's working day
            # noinspection PyUnresolvedReferences
            work_start = datetime.combine(current_date, schedule.opening_time)
            # noinspection PyUnresolvedReferences
            work_end = datetime.combine(current_date, schedule.closing_time)

            # Make work boundaries timezone-aware if the current timezone setting is active
            if timezone.is_aware(timezone.now()):
                tz = timezone.get_current_timezone()
                work_start = timezone.make_aware(work_start, tz)
                work_end = timezone.make_aware(work_end, tz)

            slots = []
            cursor = work_start

            # Iterate over time slots in fixed step increments
            while cursor + duration <= work_end:
                slot_end = cursor + duration

                # Check if proposed slot overlaps with any reserved appointment interval
                overlaps = any(
                    cursor < busy_end and slot_end > busy_start
                    for busy_start, busy_end in busy_intervals
                )

                if not overlaps:
                    slots.append(
                        {
                            "start": cursor.time().strftime("%H:%M"),
                            "end": slot_end.time().strftime("%H:%M"),
                        }
                    )

                cursor += step

            result[current_date.isoformat()] = slots
            current_date += timedelta(days=1)

        return Response(result)


class StatusTransitionConflict(APIException):
    # Custom API exception to handle invalid state machine status changes with 409 Conflict
    status_code = http_status.HTTP_409_CONFLICT
    default_detail = "Недопустимий перехід статусу."
    default_code = "status_transition_conflict"


class MasterUpdateAppointmentStatusView(generics.UpdateAPIView):
    """
    PATCH /api/appointments/<id>/status/

    Allows a master to update the status of their assigned appointment.
    Request body: {"status": "confirmed"}
    If status is "canceled", cancellation_reason is required.

    Allowed transitions:
    pending -> confirmed, canceled
    confirmed -> in_progress, canceled
    in_progress -> completed
    completed -> (none, final status)
    canceled -> (none, final status)
    """

    ALLOWED_TRANSITIONS = {
        "pending": ["confirmed", "cancelled"],
        "confirmed": ["in_progress", "cancelled"],
        "in_progress": ["completed"],
        "completed": [],
        "cancelled": [],
    }

    serializer_class = MasterStatusUpdateSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["patch"]

    def get_queryset(self) -> QuerySet[Appointment]:
        # Master can update status only for their assigned appointments
        return Appointment.objects.filter(master__user=self.request.user)

    def perform_update(self, serializer) -> None:
        appointment = self.get_object()
        new_status = serializer.validated_data.get("status")
        current_status = appointment.status

        allowed_next_statuses = self.ALLOWED_TRANSITIONS.get(current_status, [])

        if new_status not in allowed_next_statuses:
            raise StatusTransitionConflict(
                "Неможливо перевести бронювання зі статусу '%s' у статус '%s'."
                % (current_status, new_status)
            )

        if new_status == "completed":
            serializer.save(completed_at=timezone.now())
        else:
            serializer.save()

        # Trigger background email notification task to inform client of status change
        send_email_task.delay(
            recipient=appointment.client.email,
            subject="Оновлення статусу вашого запису",
            context={
                "customer_name": appointment.client.get_full_name() or appointment.client.email,
                "booking_status": appointment.get_status_display(),
                "salon_name": appointment.salon.name,
                "master_name": appointment.master.user.get_full_name() or appointment.master.user.email,
                "service_name": appointment.service.name,
                "booking_date": appointment.start.date().isoformat(),
                "booking_time": appointment.start.time().strftime("%H:%M"),
                "notification_message": "Статус вашого запису оновлено на '%s'." % appointment.get_status_display(),
            },
        )


class MasterAppointmentListView(generics.ListAPIView):
    """
    GET /api/appointments/master/active/

    Returns active appointments (pending, confirmed, in_progress) assigned to
    the currently authenticated master.

    Filters: ?appointment_date=2026-08-01&status=confirmed&client=<email substring>&service=<name substring>
    Sorting: ?ordering=start | created_at | status | service__price (prefix with '-' for descending)
    Pagination: ?page=2
    """

    serializer_class = MasterAppointmentListSerializer
    permission_classes = [IsMaster]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = MasterAppointmentFilter
    ordering_fields = ["start", "created_at", "status", "service__price"]
    ordering = ["-start"]

    def get_queryset(self) -> QuerySet[Appointment]:
        # Retrieve active appointments assigned to the master and select related FKs for optimization
        return Appointment.objects.filter(
            master__user=self.request.user,
            status__in=["pending", "confirmed", "in_progress"],
        ).select_related("client", "service", "salon")

    def filter_queryset(self, queryset) -> QuerySet[Appointment]:
        # Validate filter parameters explicitly to return HTTP 400 Bad Request on invalid input
        filterset = self.filterset_class(self.request.query_params, queryset=queryset)
        if not filterset.is_valid():
            raise serializers.ValidationError(filterset.errors)
        queryset = filterset.qs

        # Validate ordering query param against allowed fields
        ordering_param = self.request.query_params.get("ordering")
        if ordering_param:
            requested_fields = [f.lstrip("-") for f in ordering_param.split(",")]
            invalid_fields = [f for f in requested_fields if f not in self.ordering_fields]
            if invalid_fields:
                raise serializers.ValidationError(
                    {"ordering": "Недопустимі поля сортування: %s" % ", ".join(invalid_fields)}
                )

        return super().filter_queryset(queryset)


class MasterAppointmentDetailView(generics.RetrieveAPIView):
    """
    GET /api/appointments/master/<id>/

    Returns detailed information about a specific appointment assigned to
    the currently authenticated master.
    """

    serializer_class = MasterAppointmentDetailSerializer
    permission_classes = [IsMaster]

    def get_queryset(self) -> QuerySet[Appointment]:
        # Ensure masters can only retrieve details of their own appointments
        return Appointment.objects.filter(master__user=self.request.user).select_related(
            "client", "service", "salon"
        )


class MasterAppointmentHistoryView(generics.ListAPIView):
    """
    GET /api/appointments/master/history/

    Returns completed and canceled appointments assigned to the currently
    authenticated master.

    Filters: ?date_from=2026-07-01&date_to=2026-07-31&status=completed&client=<email substring>&service=<name substring>
    Sorting: ?ordering=start | created_at | status | service__price (prefix with '-' for descending)
    Pagination: ?page=2
    """

    serializer_class = MasterAppointmentHistorySerializer
    permission_classes = [IsMaster]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = MasterAppointmentHistoryFilter
    ordering_fields = ["start", "created_at", "status", "service__price"]
    ordering = ["-start"]

    def get_queryset(self) -> QuerySet[Appointment]:
        # Fetch completed or canceled historical records for the logged-in master
        return Appointment.objects.filter(
            master__user=self.request.user,
            status__in=["completed", "cancelled"],
        ).select_related("client", "service")

    def filter_queryset(self, queryset) -> QuerySet[Appointment]:
        # Explicit validation for filter and ordering query parameters
        filterset = self.filterset_class(self.request.query_params, queryset=queryset)
        if not filterset.is_valid():
            raise serializers.ValidationError(filterset.errors)
        queryset = filterset.qs

        ordering_param = self.request.query_params.get("ordering")
        if ordering_param:
            requested_fields = [f.lstrip("-") for f in ordering_param.split(",")]
            invalid_fields = [f for f in requested_fields if f not in self.ordering_fields]
            if invalid_fields:
                raise serializers.ValidationError(
                    {"ordering": "Недопустимі поля сортування: %s" % ", ".join(invalid_fields)}
                )

        return super().filter_queryset(queryset)
