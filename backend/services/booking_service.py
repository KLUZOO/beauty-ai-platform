from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from users.models import Master, WorkingSchedule, DayOff
from beauty_service.models import Service
from appointments.models import Appointment


class BookingSlotService:
    SLOT_STEP_MINUTES = 15

    @classmethod
    def get_available_slots(cls, master_id: int, service_id: int, target_date: datetime.date) -> list[str]:
        # 1. Checking the availability of the wizard and the service
        try:
            master = Master.objects.get(pk=master_id)
        except Master.DoesNotExist:
            raise NotFound("Master not found.")

        try:
            service = Service.objects.get(pk=service_id, is_active=True)
        except Service.DoesNotExist:
            raise NotFound("Service not found or inactive.")

        if not master.services.filter(pk=service.pk).exists():
            raise ValidationError("Master does not offer this service.")

        # 2. DayOff (vacation/sick leave) check
        is_day_off = DayOff.objects.filter(
            master=master,
            start_date__lte=target_date,
            end_date__gte=target_date,
        ).exists()

        if is_day_off:
            return []

        # 3. Checking the work schedule by day of the week (1 = Mon, 7 = Sun)
        weekday = target_date.isoweekday()
        schedule = WorkingSchedule.objects.filter(
            master=master,
            weekday=weekday,
            is_working_day=True,
        ).first()

        if not schedule or not schedule.start_time or not schedule.end_time:
            return []

        # Form datetime boundaries of the working day
        work_start = timezone.make_aware(datetime.combine(target_date, schedule.start_time))
        work_end = timezone.make_aware(datetime.combine(target_date, schedule.end_time))

        # 4. Get existing master records for this date
        existing_appointments = Appointment.objects.filter(
            master=master,
            start__date=target_date,
        ).exclude(status="cancelled")

        # 5. Генерація та фільтрація слотів
        available_slots = []
        service_duration = timedelta(minutes=service.duration_minutes)
        slot_step = timedelta(minutes=cls.SLOT_STEP_MINUTES)
        now = timezone.now()

        current_slot_start = work_start

        while current_slot_start + service_duration <= work_end:
            current_slot_end = current_slot_start + service_duration

            # Check: slot is not in the past
            if current_slot_start < now:
                current_slot_start += slot_step
                continue

            # Check for intersection with existing `Appointment`
            # A slot intersects if: (SlotStart < AppEnd) AND (SlotEnd > AppStart)
            has_conflict = False
            for app in existing_appointments:
                if current_slot_start < app.end and current_slot_end > app.start:
                    has_conflict = True
                    break

            if not has_conflict:
                # Store the time in a convenient "HH:MM" format
                available_slots.append(current_slot_start.strftime("%H:%M"))

            current_slot_start += slot_step

        return available_slots
