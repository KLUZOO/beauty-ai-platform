from rest_framework.routers import DefaultRouter

from referral_events.views import (
    ReferralEventViewSet,
)

app_name = "referral_events"

router = DefaultRouter()
router.register("", ReferralEventViewSet, basename="referral_event")

urlpatterns = router.urls
