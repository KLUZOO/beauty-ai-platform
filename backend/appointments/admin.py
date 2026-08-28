from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client",
        "master",
        "salon",
        "service",
        "start",
        "end",
        "status",
    )
    list_filter = ("status", "start")
    search_fields = ("client__email", "master__user__email")
