from datetime import (
    datetime,
    timedelta
)

from django_filters import OrderingFilter

from beauty_service.models import Service
from django.db.models import (
    QuerySet,
    Q
)

from django.db import transaction as db_transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)

from rest_framework import (
    filters,
    serializers
)
from rest_framework import status as http_status
from rest_framework.exceptions import (
    APIException,
    PermissionDenied
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import (
    generics,
    permissions
)

from salons.models import Salon

from tasks.notification import (
    send_email_task,
    send_appointment_event_task
)

from users.models import Master
from users.permissions import IsMaster

from appointments.services.availability import (
    InvalidDateError,
    MasterNotFoundError,
    ServiceNotAssignedError,
    ServiceNotFoundError,
    SlotService,
)
from .filters import (
    MasterAppointmentFilter,
    MasterAppointmentHistoryFilter,
    AppointmentListFilter,
    AppointmentHistoryFilter
)
from .mixins import StrictFilterOrderingMixin

from .models import Appointment

from .serializers import (
    AppointmentSerializer,
    AvailableSlotSerializer,
    AvailableSlotsQuerySerializer,
    CancelSerializer,
    MasterAppointmentDetailSerializer,
    MasterAppointmentHistorySerializer,
    MasterAppointmentListSerializer,
    MasterStatusUpdateSerializer,
    RescheduleSerializer,
    CreateAppointmentSerializer,
    AppointmentDetailSerializer,
    AppointmentListSerializer,
    AppointmentHistorySerializer
)


@extend_schema(
    summary="List client appointments",
    description="Retrieve a list of reservations for the currently authenticated client.",
    parameters=[
        OpenApiParameter(
            name="status",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter appointments by status (e.g. pending, confirmed, completed, cancelled, in_progress, no_show)",
            enum=[
                "pending",
                "confirmed",
                "in_progress",
                "completed",
                "cancelled",
                "no_show",
            ],
        ),
        OpenApiParameter(
            name="ordering",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Which field to use when ordering the results. Options: `start`, `created_at`. Prefix with `-` for descending order (e.g. `-start`). Default is `-start`.",
            enum=["start", "-start", "created_at", "-created_at"],
        ),
    ],
    responses={
        200: AppointmentSerializer(many=True),
        401: OpenApiResponse(
            description="Authentication credentials were not provided"
        ),
    },
)
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


@extend_schema(
    summary="Get Appointment List",
    description=(
        "Retrieve a paginated list of appointments with role-based access control, "
        "filtering (by date, status, salon, master, service, client), and sorting."
    ),
    parameters=[
        OpenApiParameter(
            name="client",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by client name/email (Administrators only).",
        ),
        OpenApiParameter(
            name="ordering",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description=(
                "Which field to use when ordering the results. Options: `start`, `created_at`, `status`. "
                "Prefix with `-` for descending order (e.g. `-start`). Default is `-start`."
            ),
            enum=["start", "-start", "created_at", "-created_at", "status", "-status"],
        ),
    ],
    responses={
        200: AppointmentListSerializer(many=True),
        401: OpenApiResponse(description="Authentication credentials were not provided"),
        403: OpenApiResponse(description="You do not have permission to perform this action"),
    },
)
class AppointmentListView(generics.ListAPIView):
    """
    GET /api/v1/appointments/

    Provides a paginated list of appointments with filtering and sorting capabilities.
    Access scope is restricted based on user role:
      - Clients see only their own appointments.
      - Masters see appointments assigned to them.
      - Admins see all appointments and can filter by client.
    """

    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AppointmentListFilter

    ordering_fields = ["start", "created_at", "status"]
    ordering = ["-start"]

    def get_queryset(self) -> QuerySet[Appointment]:
        user = self.request.user
        queryset = Appointment.objects.select_related("client", "master", "salon", "service")

        # Prevent non-admins from filtering by "client"
        if "client" in self.request.query_params and not (user.is_staff or user.is_superuser):
            raise PermissionDenied("Фільтрація за клієнтом доступна тільки адміністраторам.")

        # Admins have access to all records
        if user.is_staff or user.is_superuser:
            return queryset.all()

        # Masters only see records assigned to them
        if hasattr(user, "master_profile"):
            return queryset.filter(master=user.master_profile)
        if hasattr(user, "master"):
            return queryset.filter(master=user.master)

        # Regular clients only see their own records
        return queryset.filter(client=user)


@extend_schema(
    summary="Reschedule client appointment",
    description="Moves an existing customer reservation to a new datetime interval.",
    request=RescheduleSerializer,
    responses={
        200: RescheduleSerializer,
        400: OpenApiResponse(
            description="Validation error (e.g., end time is before start time, or appointment is already completed/cancelled)"
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided"
        ),
        404: OpenApiResponse(
            description="Appointment not found or does not belong to the user"
        ),
    },
)
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


@extend_schema(
    summary="Cancel client appointment",
    description="Cancels the customer's upcoming booking (sets the status to 'cancelled'). Request body is optional.",
    request=CancelSerializer,
    responses={
        200: CancelSerializer,
        400: OpenApiResponse(
            description="Validation error (e.g. appointment is already completed or cancelled)"
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided"
        ),
        404: OpenApiResponse(
            description="Appointment not found or does not belong to the user"
        ),
    },
)
class CancelAppointmentView(generics.UpdateAPIView):
    """
    PATCH /api/appointments/<id>/cancel/

    Cancel an appointment (BE-BOOKING-04).
    Allowed for:
    - Client (own appointments)
    - Master (assigned appointments)
    - Administrator (any appointments)
    """
    serializer_class = CancelSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["patch"]
    queryset = Appointment.objects.all()

    def get_object(self) -> Appointment:
        appointment = super().get_object()
        user = self.request.user

        # Checking roles and access rights
        is_admin = user.is_staff or user.is_superuser
        is_client = appointment.client == user
        is_master = hasattr(appointment.master, "user") and appointment.master.user == user

        if not (is_admin or is_client or is_master):
            raise PermissionDenied("У вас немає прав для скасування цього запису.")

        return appointment

    def perform_update(self, serializer) -> None:
        appointment = self.get_object()

        # Check the status of the recording
        if appointment.status == "cancelled":
            raise serializers.ValidationError({"detail": "Запис вже скасовано."})

        if appointment.status == "completed":
            raise serializers.ValidationError({"detail": "Неможливо скасувати вже завершений запис."})

        # Check the time (only future recordings)
        if appointment.start <= timezone.now():
            raise serializers.ValidationError({"detail": "Неможливо скасувати минулий запис."})

        # Save the reason for cancellation and change the status
        reason = serializer.validated_data.get("cancellation_reason", "")
        if hasattr(appointment, "cancellation_reason"):
            appointment.cancellation_reason = reason
        elif reason and hasattr(appointment, "notes"):
            appointment.notes = f"{appointment.notes}\nПричина скасування: {reason}".strip()

        appointment.status = "cancelled"
        appointment.save()

        # 5. Відправка email-сповіщень (Клієнту та Майстру)
        if appointment.client and appointment.client.email:
            send_email_task.delay(
                recipient=appointment.client.email,
                subject="Скасування бронювання",
                context={
                    "customer_name": appointment.client.get_full_name() or appointment.client.email,
                    "service_name": appointment.service.name,
                    "booking_date": timezone.localtime(appointment.start).strftime("%Y-%m-%d"),
                    "booking_time": timezone.localtime(appointment.start).strftime("%H:%M"),
                    "reason": reason or "Не вказано",
                }
            )

        if appointment.master and appointment.master.user and appointment.master.user.email:
            send_email_task.delay(
                recipient=appointment.master.user.email,
                subject="Скасування бронювання клієнтом",
                context={
                    "master_name": appointment.master.user.get_full_name() or appointment.master.user.email,
                    "customer_name": appointment.client.get_full_name() or appointment.client.email,
                    "service_name": appointment.service.name,
                    "booking_date": timezone.localtime(appointment.start).strftime("%Y-%m-%d"),
                    "booking_time": timezone.localtime(appointment.start).strftime("%H:%M"),
                    "reason": reason or "Не вказано",
                }
            )


@extend_schema(
    summary="Get available booking slots",
    description=(
            "Returns a list of available time slots for booking, grouped by date.\n\n"
            "Required query parameters: `salon`, `master`, `service`, `date_from`."
    ),
    parameters=[
        OpenApiParameter(
            name="salon",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=True,
            description="ID of the salon (used to fetch daily working hours)",
        ),
        OpenApiParameter(
            name="master",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=True,
            description="ID of the master (used to query busy time ranges)",
        ),
        OpenApiParameter(
            name="service",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=True,
            description="ID of the service (used to compute required slot duration)",
        ),
        OpenApiParameter(
            name="date_from",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Start date for slot lookup (format: YYYY-MM-DD)",
        ),
        OpenApiParameter(
            name="date_to",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            required=False,
            description="End date for slot lookup (format: YYYY-MM-DD, inclusive; defaults to date_from)",
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Map of dates to array of available time slots",
            examples=[
                OpenApiExample(
                    name="Available slots example",
                    value={
                        "2026-08-01": [
                            {"start": "10:00", "end": "10:45"},
                            {"start": "10:15", "end": "11:00"},
                        ],
                        "2026-08-02": [],
                    },
                )
            ],
        ),
        400: OpenApiResponse(
            description="Validation error (missing required parameters, invalid date format, or invalid IDs)"
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided"
        ),
    },
)
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
            busy_intervals = [(a.start, a.end) for a in busy_appointments]

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


@extend_schema(
    summary="Update appointment status by master",
    description=(
        "Allows an authenticated master to update the status of their assigned appointment.\n\n"
        "**Allowed status transitions:**\n"
        "- `pending` ➔ `confirmed`, `cancelled`\n"
        "- `confirmed` ➔ `in_progress`, `cancelled`\n"
        "- `in_progress` ➔ `completed`\n"
        "- `completed` ➔ (none, final status)\n"
        "- `cancelled` ➔ (none, final status)\n\n"
        "**Note:** If status is set to `cancelled`, `cancellation_reason` is required."
    ),
    request=MasterStatusUpdateSerializer,
    responses={
        200: MasterStatusUpdateSerializer,
        400: OpenApiResponse(
            description="Validation error (e.g. missing cancellation_reason when status='cancelled')"
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided"
        ),
        403: OpenApiResponse(
            description="Permission denied or appointment not assigned to this master"
        ),
        404: OpenApiResponse(description="Appointment not found"),
        409: OpenApiResponse(
            description="Status transition conflict (e.g. invalid status transition like completed ➔ in_progress)"
        ),
    },
)
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
                "Неможливо перевести бронювання зі статусом '%s' у статус '%s'."
                % (current_status, new_status)
            )

        # Atomic transaction + on_commit notification for BE-BOOKING-07
        with db_transaction.atomic():
            if new_status == "completed":
                appointment = serializer.save(completed_at=timezone.now())
            else:
                appointment = serializer.save()

            # Mapping status to required Event Types
            event_type_map = {
                "confirmed": "CONFIRMED",
                "cancelled": "CANCELLED",
                "completed": "COMPLETED",
            }

            if new_status in event_type_map:
                payload = {
                    "appointment_id": appointment.id,
                    "client_id": appointment.client_id,
                    "master_id": appointment.master_id,
                    "salon_id": appointment.salon_id,
                    "service_id": appointment.service_id,
                    "appointment_date": timezone.localtime(appointment.start).date().isoformat(),
                    "appointment_time": timezone.localtime(appointment.start).strftime("%H:%M"),
                    "appointment_status": appointment.status,
                    "event_type": event_type_map[new_status],
                    "timestamp": timezone.now().isoformat(),
                }

                # Executed strictly after successful database commit
                db_transaction.on_commit(lambda: send_appointment_event_task.delay(payload))

            # Legacy email notification registered within transaction context
            db_transaction.on_commit(
                lambda: send_email_task.delay(
                    recipient=appointment.client.email,
                    subject="Оновлення статусу вашого запису",
                    context={
                        "customer_name": appointment.client.get_full_name()
                                         or appointment.client.email,
                        "booking_status": appointment.get_status_display(),
                        "salon_name": appointment.salon.name,
                        "master_name": appointment.master.user.get_full_name()
                                       or appointment.master.user.email,
                        "service_name": appointment.service.name,
                        "booking_date": timezone.localtime(appointment.start).date().isoformat(),
                        "booking_time": timezone.localtime(appointment.start).strftime("%H:%M"),
                        "notification_message": "Статус вашого запису оновлено на '%s'."
                                                % appointment.get_status_display(),
                    },
                )
            )


@extend_schema(
    summary="List active master appointments",
    description="Returns active appointments (pending, confirmed, in_progress) assigned to the current master.",
    parameters=[
        OpenApiParameter(
            "appointment_date",
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            description="Filter by date (YYYY-MM-DD)",
        ),
        OpenApiParameter(
            "status",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Filter by status (pending, confirmed, in_progress)",
        ),
        OpenApiParameter(
            "client",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Filter by client email (contains)",
        ),
        OpenApiParameter(
            "service",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Filter by service name (contains)",
        ),
        OpenApiParameter(
            "ordering",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Ordering: start, created_at, status, service__price (prefix with '-' for descending)",
        ),
    ],
)
class MasterAppointmentListView(StrictFilterOrderingMixin, generics.ListAPIView):
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


@extend_schema(
    summary="Get master appointment detail",
    description="Retrieve detailed information about a specific appointment assigned to the currently authenticated master.",
    responses={
        200: MasterAppointmentDetailSerializer,
        401: OpenApiResponse(
            description="Authentication credentials were not provided"
        ),
        403: OpenApiResponse(description="Permission denied (Requires master profile)"),
        404: OpenApiResponse(
            description="Appointment not found or not assigned to this master"
        ),
    },
)
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
        return Appointment.objects.filter(
            master__user=self.request.user
        ).select_related("client", "service", "salon")


@extend_schema(
    summary="List master appointment history",
    description="Returns completed and canceled appointments assigned to the currently authenticated master.",
    parameters=[
        OpenApiParameter(
            "date_from",
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            description="Filter from this date (YYYY-MM-DD)",
        ),
        OpenApiParameter(
            "date_to",
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            description="Filter to this date (YYYY-MM-DD)",
        ),
        OpenApiParameter(
            "status",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Filter by status (completed, cancelled)",
        ),
        OpenApiParameter(
            "client",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Filter by client email (contains)",
        ),
        OpenApiParameter(
            "service",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Filter by service name (contains)",
        ),
        OpenApiParameter(
            "ordering",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Ordering: start, created_at, status, service__price (prefix with '-' for descending)",
        ),
    ],
)
class MasterAppointmentHistoryView(StrictFilterOrderingMixin, generics.ListAPIView):
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


class AvailableTimeSlotsView(APIView):
    """
    GET /api/appointments/available-slots/?master_id=1&service_id=2&date=2026-08-15
    """

    permission_classes = [AllowAny]

    # noinspection PyMethodMayBeStatic
    def get(self, request) -> Response:
        query = AvailableSlotsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data

        slot_service = SlotService(
            master_id=params["master_id"],
            service_id=params["service_id"],
            target_date=params["date"],
        )

        try:
            slots = slot_service.generate()
        except MasterNotFoundError:
            return Response({"detail": "Master not found."}, status=http_status.HTTP_404_NOT_FOUND)
        except ServiceNotFoundError:
            return Response({"detail": "Service not found."}, status=http_status.HTTP_404_NOT_FOUND)
        except ServiceNotAssignedError:
            return Response(
                {"detail": "The selected service is not assigned to this master."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        except InvalidDateError:
            return Response(
                {"detail": "Appointment date cannot be in the past."},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        result = AvailableSlotSerializer(slots, many=True)
        return Response(result.data, status=http_status.HTTP_200_OK)


class CreateAppointmentView(generics.CreateAPIView):
    """
    POST /api/appointments/
    Creating a new client record (BE-BOOKING-02 / BE-CLIENT-08 / BE-BOOKING-03 / BE-BOOKING-07).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CreateAppointmentSerializer

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            master = Master.objects.get(pk=data["master_id"])
        except Master.DoesNotExist:
            return Response({"detail": "Майстра не знайдено."}, status=http_status.HTTP_404_NOT_FOUND)

        try:
            service = Service.objects.get(pk=data["service_id"], is_active=True)
        except Service.DoesNotExist:
            return Response({"detail": "Послугу не знайдено."}, status=http_status.HTTP_404_NOT_FOUND)

        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(
            datetime.combine(data["appointment_date"], data["appointment_time"]),
            tz
        )
        end_dt = start_dt + timedelta(minutes=service.duration_minutes)

        if start_dt <= timezone.now():
            return Response(
                {"detail": "Час запису повинен бути у майбутньому."},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        slot_service = SlotService(
            master_id=master.id,
            service_id=service.id,
            target_date=data["appointment_date"]
        )
        try:
            available_slots = slot_service.generate()
        except ServiceNotAssignedError:
            return Response(
                {"detail": "Обрана послуга не надається цим майстром."},
                status=http_status.HTTP_400_BAD_REQUEST
            )
        except (MasterNotFoundError, ServiceNotFoundError, InvalidDateError) as e:
            return Response({"detail": str(e)}, status=http_status.HTTP_400_BAD_REQUEST)

        req_start_str = data["appointment_time"].strftime("%H:%M")
        is_slot_available = any(s["start"] == req_start_str for s in available_slots)

        if not is_slot_available:
            return Response(
                {"detail": "Обраний час недоступний (поза робочим графіком, вихідний або перерва)."},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        # Protection against Concurrency + Notification publishing inside transaction context
        with db_transaction.atomic():
            has_conflict = Appointment.objects.select_for_update().filter(
                master=master,
                start__lt=end_dt,
                end__gt=start_dt
            ).exclude(status__in=["cancelled", "no_show"]).exists()

            if has_conflict:
                return Response(
                    {"detail": "Обраний слот вже зайнятий іншим бронюванням."},
                    status=http_status.HTTP_409_CONFLICT
                )

            appointment = Appointment.objects.create(
                client=request.user,
                master=master,
                salon=master.salon,
                service=service,
                start=start_dt,
                end=end_dt,
                notes=data.get("notes", ""),
                status="pending"
            )

            # Notification payload for BE-BOOKING-07
            payload = {
                "appointment_id": appointment.id,
                "client_id": appointment.client_id,
                "master_id": appointment.master_id,
                "salon_id": appointment.salon_id,
                "service_id": appointment.service_id,
                "appointment_date": timezone.localtime(appointment.start).date().isoformat(),
                "appointment_time": timezone.localtime(appointment.start).strftime("%H:%M"),
                "appointment_status": appointment.status,
                "event_type": "CREATED",
                "timestamp": timezone.now().isoformat(),
            }

            # Published ONLY after the transaction is successfully committed
            db_transaction.on_commit(lambda: send_appointment_event_task.delay(payload))

        response_serializer = AppointmentSerializer(appointment)
        return Response(response_serializer.data, status=http_status.HTTP_201_CREATED)


class AppointmentDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/appointments/<id>/

    Get detailed information about a specific appointment (BE-BOOKING-05).
    """
    serializer_class = AppointmentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Appointment.objects.select_related("client", "master", "salon", "service").all()

    def get_object(self) -> Appointment:
        appointment = super().get_object()
        user = self.request.user

        # Roles
        is_admin = user.is_staff or user.is_superuser
        is_client = appointment.client == user

        # Check the master (whether the user is bound to the master)
        is_master = False
        if appointment.master:
            master_user = getattr(appointment.master, "user", None)
            if master_user == user:
                is_master = True

        # Rights check
        if not (is_admin or is_client or is_master):
            raise PermissionDenied("У вас немає доступу до перегляду цього запису.")

        return appointment


class AppointmentHistoryView(generics.ListAPIView):
    serializer_class = AppointmentHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AppointmentHistoryFilter
    ordering_fields = ["start", "created_at", "status"]
    ordering = ["-start"]

    def get_queryset(self) -> QuerySet[Appointment, Appointment]:
        user = self.request.user
        now = timezone.now()

        # Role differentiation
        role = getattr(user, "role", "").upper()
        if role == "ADMIN" or user.is_staff or user.is_superuser:
            qs = Appointment.objects.all()
        elif role == "MASTER" or hasattr(user, "master_profile"):
            qs = Appointment.objects.filter(master__user=user)
        else:
            qs = Appointment.objects.filter(client=user)

        # Filtering historical records:
        # The sample includes: completed, canceled, no_show OR those where the start time has already passed
        historical_statuses = ["completed", "cancelled", "no_show"]
        active_statuses = ["pending", "confirmed", "in_progress"]

        return qs.filter(
            Q(status__in=historical_statuses) |
            Q(start__lt=now)
        ).exclude(
            # Exclude future/active entries
            status__in=active_statuses,
            start__gte=now
        ).select_related("client", "master", "salon", "service")
