from django.conf import settings
from django.db import models


class SearchQuery(models.Model):
    class SearchType(models.TextChoices):
        AI_SEARCH = "ai_search", "AI search"
        MANUAL = "manual", "Manual"
        QUICK_FILTER = "quick_filter", "Quick filter"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="search_queries",
    )

    query_text = models.TextField()

    search_type = models.CharField(
        max_length=20,
        choices=SearchType.choices,
    )

    search_datetime = models.DateTimeField(auto_now_add=True)

    recommended_service = models.ForeignKey(
        "beauty_service.Service",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="search_recommendations",
    )

    recommended_salon = models.ForeignKey(
        "salons.Salon",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="search_recommendations",
    )

    recommended_master = models.ForeignKey(
        "users.Master",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="search_recommendations",
    )

    recommendation_accepted = models.BooleanField(default=False)

    click = models.ForeignKey(
        "search.UserClick",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    def __str__(self):
        return f"{self.search_type}: {self.query_text[:50]}"


class UserClick(models.Model):
    class SearchType(models.TextChoices):
        AI_SEARCH = "ai_search", "AI search"
        MANUAL = "manual", "Manual"
        QUICK_FILTER = "quick_filter", "Quick filter"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clicks",
    )

    search_type = models.CharField(
        max_length=20,
        choices=SearchType.choices,
    )

    quick_filter_label = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    service = models.ForeignKey(
        "beauty_service.Service",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user_clicks",
    )

    salon = models.ForeignKey(
        "salons.Salon",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user_clicks",
    )

    master = models.ForeignKey(
        "users.Master",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user_clicks",
    )

    click_datetime = models.DateTimeField(
        auto_now_add=True,
    )

    led_to_booking = models.BooleanField(
        default=False,
    )

    appointment = models.ForeignKey(
        "appointments.Appointment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="user_clicks",
    )

    def __str__(self):
        return f"{self.search_type} click — {self.click_datetime}"
