from django.contrib import admin

from .models import (
    Salon,
    SalonWorkingHours,
    CachedSalon
)


class SalonWorkingHoursInline(admin.TabularInline):
    model = SalonWorkingHours
    extra = 0


@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "address", "owner")
    list_filter = ("city",)
    search_fields = ("name", "address")
    inlines = [SalonWorkingHoursInline]


@admin.register(CachedSalon)
class CachedSalonAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "address", "last_used_at")
    list_filter = ("city",)
    search_fields = ("name", "address")
