from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "appointment",
        "client",
        "master",
        "rating",
        "created_at",
    )
    list_filter = ("rating",)
    search_fields = (
        "appointment__client__email",
        "appointment__master__user__email",
        "comment",
    )

    @admin.display(description="Client")
    def client(self, obj):
        return obj.appointment.client

    @admin.display(description="Master")
    def master(self, obj):
        return obj.appointment.master
