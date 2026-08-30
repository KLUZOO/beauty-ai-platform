from datetime import date, datetime, time, timedelta

from appointments.models import Appointment
from django.db.models import Prefetch, QuerySet
from users.models import Master, MasterStatus, WorkingSchedule

from beauty_service.models import Service


class AvailableMastersService:
    @staticmethod
    def _get_ids_available_masters_by_duration_and_datetime(
        masters: QuerySet[Master],
        current_date: date,
        start_time: time,
        end_time: time,
        duration: int,
    ) -> set:
        weekday = current_date.isoweekday()

        work_start_datetime = datetime.combine(
            current_date,
            start_time,
        )
        work_end_datetime = datetime.combine(
            current_date,
            end_time,
        )

        schedules = WorkingSchedule.objects.filter(
            weekday=weekday,
            is_working_day=True,
            start_time__lte=end_time,
            end_time__gte=start_time,
        )

        appointments = (
            Appointment.objects.filter(
                start__lt=work_end_datetime,
                end__gt=work_start_datetime,
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
                    "appointments",
                    queryset=appointments,
                ),
            )
            .distinct()
        )

        available_master_ids = set()
        duration_delta = timedelta(minutes=duration)
        for master in masters:
            schedule = master.working_schedule.first()

            if schedule is None:
                continue

            work_start = max(
                schedule.start_time,
                start_time,
            )
            work_end = min(
                schedule.end_time,
                end_time,
            )

            work_start_datetime = datetime.combine(
                current_date,
                work_start,
            )
            work_end_datetime = datetime.combine(
                current_date,
                work_end,
            )

            current_start = work_start_datetime

            for appointment in master.appointments.all():
                appointment_start = max(
                    appointment.start,
                    work_start_datetime,
                )

                if appointment_start - current_start >= duration_delta:
                    available_master_ids.add(master.id)
                    break

                current_start = max(
                    current_start,
                    min(
                        appointment.end,
                        work_end_datetime,
                    ),
                )

            else:
                if work_end_datetime - current_start >= duration_delta:
                    available_master_ids.add(master.id)

        return available_master_ids

    @staticmethod
    def get_ids_available_masters_by_service(
        masters: QuerySet[Master],
        service: Service,
        datetime_from: datetime,
        datetime_to: datetime,
    ) -> set:
        duration = service.duration_minutes

        available_masters = masters.filter(
            account_status=MasterStatus.ACTIVE,
            services=service,
        ).distinct()

        current_date = datetime_from.date()
        available_master_ids = set()

        while current_date <= datetime_to.date():
            if current_date == datetime_from.date():
                start_time = datetime_from.time()
            else:
                start_time = time.min

            if current_date == datetime_to.date():
                end_time = datetime_to.time()
            else:
                end_time = time.max

            available_master_ids.update(
                AvailableMastersService._get_ids_available_masters_by_duration_and_datetime(
                    masters=available_masters,
                    current_date=current_date,
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                )
            )

            available_masters = available_masters.exclude(id__in=available_master_ids)

            current_date += timedelta(days=1)

        return available_master_ids
