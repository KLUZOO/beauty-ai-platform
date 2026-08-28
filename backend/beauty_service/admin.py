from django.contrib import admin

from .models import (
    Service,
    ServiceCategory
)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "duration_minutes", "price")
    list_filter = ("category",)
    search_fields = ("name",)
