from __future__ import annotations

from datetime import date as date_cls, datetime, time, timedelta

from django.utils import timezone

from beauty_service.models import Service
from users.models import DayOff, Master, MasterBreak, MasterService, WorkingSchedule


class MasterNotFoundError(Exception):
    pass


class ServiceNotFoundError(Exception):
    pass


class ServiceNotAssignedError(Exception):
    pass


class InvalidDateError(Exception):
    pass


class AvailableSlot:
    __slots__ = ("start", "end")

    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end

    def as_dict(self) -> dict:
        return {
            "start_time": timezone.localtime(self.start).isoformat(),
            "end_time": timezone.localtime(self.end).isoformat(),
            "availability_status": "available",
        }


class SlotService:
    """Generates available appointment time slots for a master/service/date combination."""

    def __init__(self, master_id: int, service_id: int, target_date: date_cls):
        self.master_id = master_id
        self.service_id = service_id
        self.target_date = target_date

    def generate(self) -> list[dict]:
        master = self._get_master()
        service = self._get_service()
        self._validate_service_assigned(master, service)
        self._validate_date()

        if self._is_day_off(master):
            return []

        schedule = self._get_working_schedule(master)
        if schedule is None:
            return []

        breaks = list(
            MasterBreak.objects.filter(
                master=master,
                weekday=self.target_date.isoweekday(),
            )
        )

        busy_ranges = self._get_busy_ranges(master, breaks)

        return self._build_slots(schedule, service.duration_minutes, busy_ranges)

    def _get_master(self) -> Master:
        try:
            return Master.objects.get(pk=self.master_id)
        except Master.DoesNotExist as exc:
            raise MasterNotFoundError() from exc

    def _get_service(self) -> Service:
        try:
            return Service.objects.get(pk=self.service_id, is_active=True)
        except Service.DoesNotExist as exc:
            raise ServiceNotFoundError() from exc

    # noinspection PyMethodMayBeStatic
    def _validate_service_assigned(self, master: Master, service: Service) -> None:
        assigned = MasterService.objects.filter(master=master, service=service).exists()
        if not assigned:
            raise ServiceNotAssignedError()

    def _validate_date(self) -> None:
        today = timezone.localdate()
        if self.target_date < today:
            raise InvalidDateError()

    def _is_day_off(self, master: Master) -> bool:
        return DayOff.objects.filter(
            master=master,
            start_date__lte=self.target_date,
            end_date__gte=self.target_date,
        ).exists()

    def _get_working_schedule(self, master: Master) -> WorkingSchedule | None:
        return WorkingSchedule.objects.filter(
            master=master,
            weekday=self.target_date.isoweekday(),
            is_working_day=True,
        ).first()

    def _get_busy_ranges(
        self, master: Master, breaks: list[MasterBreak]
    ) -> list[tuple[datetime, datetime]]:
        from appointments.models import Appointment

        tz = timezone.get_current_timezone()
        day_start = timezone.make_aware(datetime.combine(self.target_date, time.min), tz)
        day_end = timezone.make_aware(datetime.combine(self.target_date, time.max), tz)

        appointments = Appointment.objects.filter(
            master=master,
            start__lt=day_end,
            end__gt=day_start,
        ).exclude(status__in=["cancelled", "no_show"])

        busy = [(appt.start, appt.end) for appt in appointments]

        for brk in breaks:
            busy.append(
                (
                    timezone.make_aware(datetime.combine(self.target_date, brk.start_time), tz),
                    timezone.make_aware(datetime.combine(self.target_date, brk.end_time), tz),
                )
            )

        return busy

    def _build_slots(
        self,
        schedule: WorkingSchedule,
        duration_minutes: int,
        busy_ranges: list[tuple[datetime, datetime]],
    ) -> list[dict]:
        tz = timezone.get_current_timezone()
        duration = timedelta(minutes=duration_minutes)

        work_start = timezone.make_aware(datetime.combine(self.target_date, schedule.start_time), tz)
        work_end = timezone.make_aware(datetime.combine(self.target_date, schedule.end_time), tz)

        now = timezone.now()
        slots: list[dict] = []
        cursor = work_start

        step = timedelta(minutes=15)  # Крок сітки генерації слотів

        while cursor + duration <= work_end:
            slot_end = cursor + duration

            if cursor >= now and not self._overlaps_any(cursor, slot_end, busy_ranges):
                slots.append(AvailableSlot(cursor, slot_end).as_dict())

            cursor += step

        return slots

    @staticmethod
    def _overlaps_any(
        start: datetime, end: datetime, ranges: list[tuple[datetime, datetime]]
    ) -> bool:
        return any(start < r_end and end > r_start for r_start, r_end in ranges)
