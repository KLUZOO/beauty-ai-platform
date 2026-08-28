from rest_framework.routers import DefaultRouter

from promotions.views import (
    PromotionViewSet,
)

app_name = "promotions"

router = DefaultRouter()
router.register("", PromotionViewSet, basename="promotion")

urlpatterns = router.urls
