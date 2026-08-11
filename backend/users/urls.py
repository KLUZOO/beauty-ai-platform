from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from users.views import (
    ChangePasswordView,
    CreateUserView,
    DayOffViewSet,
    FavoriteMastersListView,
    FavoriteMasterView,
    GoogleLoginView,
    GoogleTestView,
    ManageMasterView,
    ManageUserView,
    ManageWorkingScheduleView,
    MasterListView,
    SetPasswordView,
    VerifyEmailView,
    WorkingScheduleListCreateView,
)

app_name = "users"

router = DefaultRouter()
router.register(
    "masters/me/day-offs",
    DayOffViewSet,
    basename="day-off",
)

urlpatterns = [
    path("register/", CreateUserView.as_view(), name="create"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("me/", ManageUserView.as_view(), name="manage"),
    path(
        "verify-email/",
        VerifyEmailView.as_view(),
        name="verify-email",
    ),
    path("google-login/", GoogleLoginView.as_view(), name="google-login"),
    path("google-test/", GoogleTestView.as_view(), name="google-test"),
    path("me/change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("me/set-password/", SetPasswordView.as_view(), name="set_password"),
    path("masters/me/", ManageMasterView.as_view(), name="master-profile"),
    path(
        "masters/me/working-schedule/",
        WorkingScheduleListCreateView.as_view(),
        name="working-schedule-list-create",
    ),
    path(
        "masters/me/working-schedule/<int:pk>/",
        ManageWorkingScheduleView.as_view(),
        name="working-schedule-detail",
    ),
    path("masters/", MasterListView.as_view(), name="master-list"),
    path(
        "favorite-masters/",
        FavoriteMastersListView.as_view(),
        name="favorite-masters-list",
    ),
    path(
        "favorite-masters/<int:master_id>/",
        FavoriteMasterView.as_view(),
        name="favorite-master",
    ),
] + router.urls
