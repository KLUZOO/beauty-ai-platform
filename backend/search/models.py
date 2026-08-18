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
        "services.Service",
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
