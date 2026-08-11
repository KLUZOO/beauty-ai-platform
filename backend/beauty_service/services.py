from datetime import date, datetime, time, timedelta

from appointments.models import Appointment
from django.db.models import Prefetch, QuerySet
from django.utils import timezone
from users.models import (
    Master,
    MasterBreak,
    MasterStatus,
    WorkingSchedule,
)

from beauty_service.models import Service


class AvailableMastersService:
    @staticmethod
    def _make_aware_datetime(
        current_date: date,
        current_time: time,
    ) -> datetime:
        return timezone.make_aware(
            datetime.combine(current_date, current_time),
        )

    @staticmethod
    def _get_ids_available_masters_by_duration_and_datetime(
        masters: QuerySet[Master],
        current_date: date,
        start_time: time,
        end_time: time,
        duration: int,
    ) -> set[int]:
        weekday = current_date.isoweekday()

        requested_start = AvailableMastersService._make_aware_datetime(
            current_date,
            start_time,
        )
        requested_end = AvailableMastersService._make_aware_datetime(
            current_date,
            end_time,
        )

        schedules = WorkingSchedule.objects.filter(
            weekday=weekday,
            is_working_day=True,
        )

        breaks = MasterBreak.objects.filter(
            weekday=weekday,
        )

        appointments = (
            Appointment.objects.filter(
                start__lt=requested_end,
                end__gt=requested_start,
            )
            .exclude(
                status__in=("cancelled", "pending"),
            )
            .order_by("start")
        )

        masters = (
            masters.exclude(
                days_off__start_date__lte=current_date,
                days_off__end_date__gte=current_date,
            )
            .prefetch_related(
                Prefetch(
                    "working_schedule",
                    queryset=schedules,
                ),
                Prefetch(
                    "breaks",
                    queryset=breaks,
                ),
                Prefetch(
                    "appointments",
                    queryset=appointments,
                ),
            )
            .distinct()
        )

        duration_delta = timedelta(minutes=duration)
        available_master_ids: set[int] = set()

        for master in masters:
            schedule = master.working_schedule.first()

            if schedule is None:
                continue

            # Intersect master's working hours with requested interval.
            work_start = max(
                schedule.start_time,
                start_time,
            )
            work_end = min(
                schedule.end_time,
                end_time,
            )

            if work_start >= work_end:
                continue

            work_start_datetime = AvailableMastersService._make_aware_datetime(
                current_date,
                work_start,
            )
            work_end_datetime = AvailableMastersService._make_aware_datetime(
                current_date,
                work_end,
            )

            busy_intervals: list[tuple[datetime, datetime]] = []

            # Add master's breaks.
            for master_break in master.breaks.all():
                break_start = max(
                    master_break.start_time,
                    work_start,
                )
                break_end = min(
                    master_break.end_time,
                    work_end,
                )

                if break_start >= break_end:
                    continue

                busy_intervals.append(
                    (
                        AvailableMastersService._make_aware_datetime(
                            current_date,
                            break_start,
                        ),
                        AvailableMastersService._make_aware_datetime(
                            current_date,
                            break_end,
                        ),
                    )
                )

            # Add master's appointments.
            for appointment in master.appointments.all():
                appointment_start = max(
                    appointment.start,
                    work_start_datetime,
                )
                appointment_end = min(
                    appointment.end,
                    work_end_datetime,
                )

                if appointment_start >= appointment_end:
                    continue

                busy_intervals.append(
                    (
                        appointment_start,
                        appointment_end,
                    )
                )

            # Sort all busy intervals by start time.
            busy_intervals.sort(
                key=lambda interval: interval[0],
            )

            # Merge overlapping busy intervals.
            merged_busy_intervals: list[tuple[datetime, datetime]] = []

            for busy_start, busy_end in busy_intervals:
                if not merged_busy_intervals:
                    merged_busy_intervals.append(
                        (busy_start, busy_end),
                    )
                    continue

                previous_start, previous_end = merged_busy_intervals[-1]

                if busy_start <= previous_end:
                    merged_busy_intervals[-1] = (
                        previous_start,
                        max(previous_end, busy_end),
                    )
                else:
                    merged_busy_intervals.append(
                        (busy_start, busy_end),
                    )

            # Find a free interval large enough for the service.
            current_start = work_start_datetime

            for busy_start, busy_end in merged_busy_intervals:
                free_duration = busy_start - current_start

                if free_duration >= duration_delta:
                    available_master_ids.add(master.id)
                    break

                current_start = max(
                    current_start,
                    busy_end,
                )
            else:
                free_duration = work_end_datetime - current_start

                if free_duration >= duration_delta:
                    available_master_ids.add(master.id)

        return available_master_ids

    @staticmethod
    def get_ids_available_masters_by_service(
        masters: QuerySet[Master],
        service: Service,
        datetime_from: datetime,
        datetime_to: datetime,
    ) -> set[int]:
        duration = service.duration_minutes

        if timezone.is_naive(datetime_from):
            datetime_from = timezone.make_aware(datetime_from)

        if timezone.is_naive(datetime_to):
            datetime_to = timezone.make_aware(datetime_to)

        # Convert to the project's current timezone before
        # extracting date/time/weekday.
        datetime_from = timezone.localtime(datetime_from)
        datetime_to = timezone.localtime(datetime_to)

        available_masters = masters.filter(
            account_status=MasterStatus.ACTIVE,
            services=service,
        ).distinct()

        available_master_ids: set[int] = set()

        current_date = datetime_from.date()
        last_date = datetime_to.date()

        while current_date <= last_date:
            if current_date == datetime_from.date():
                start_time = datetime_from.time()
            else:
                start_time = time.min

            if current_date == datetime_to.date():
                end_time = datetime_to.time()
            else:
                end_time = time.max

            available_ids = AvailableMastersService._get_ids_available_masters_by_duration_and_datetime(
                masters=available_masters,
                current_date=current_date,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
            )

            available_master_ids.update(available_ids)

            # A master found on an earlier date does not need
            # to be checked again.
            available_masters = available_masters.exclude(
                id__in=available_ids,
            )

            current_date += timedelta(days=1)

        return available_master_ids
