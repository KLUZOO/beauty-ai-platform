from django.contrib import admin

from .models import CachedSalon, Salon, SalonWorkingHours


class SalonWorkingHoursInline(admin.TabularInline):
    model = SalonWorkingHours
    extra = 0


@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "city",
        "address",
        "owner",
    )

    list_filter = ("location__city_name",)

    search_fields = (
        "name",
        "location__city_name",
        "location__address",
    )

    inlines = (SalonWorkingHoursInline,)

    @admin.display(description="City")
    def city(self, obj):
        return obj.location.city_name if obj.location else "-"

    @admin.display(description="Address")
    def address(self, obj):
        return obj.location.address if obj.location else "-"


@admin.register(CachedSalon)
class CachedSalonAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "city",
        "address",
        "last_used_at",
    )

    list_filter = ("location__city_name",)

    search_fields = (
        "name",
        "location__city_name",
        "location__address",
    )

    @admin.display(description="City")
    def city(self, obj):
        return obj.location.city_name if obj.location else "-"

    @admin.display(description="Address")
    def address(self, obj):
        return obj.location.address if obj.location else "-"
