from django.db.models import (
    Avg,
    Count,
    Q,
    Prefetch,
    Value
)

from django.db.models.functions import Concat
from django.shortcuts import render
from django.views import View

from rest_framework import (
    generics,
    status,
    viewsets
)
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from salons.models import Salon, SalonStatus

from users.models import (
    DayOff,
    Master,
    MasterStatus,
    WorkingSchedule
)

from users.permissions import IsMaster
from users.serializers import (
    ChangePasswordSerializer,
    DayOffSerializer,
    GoogleLoginSerializer,
    MasterListSerializer,
    MasterProfileSerializer,
    SetPasswordSerializer,
    UserProfileSerializer,
    UserSerializer,
    VerifyEmailSerializer,
    WorkingScheduleSerializer,
)
from users.services.auth_service import UserAuthService


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer


class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class ManageMasterView(generics.RetrieveUpdateAPIView):
    serializer_class = MasterProfileSerializer
    permission_classes = (IsMaster,)

    def get_object(self):
        return self.request.user.master


class MasterListView(generics.ListAPIView):
    serializer_class = MasterListSerializer
    permission_classes = (IsAuthenticated,)

    filter_backends = (OrderingFilter,)

    ordering_fields = (
        "rating",
        "name",
        "years_of_experience",
        "popularity",
    )

    ordering = ("-rating",)

    def get_queryset(self):
        return (
            Master.objects.filter(
                account_status=MasterStatus.ACTIVE,
            )
            .prefetch_related(
                Prefetch(
                    "salons",
                    queryset=Salon.objects.filter(
                        salon_status=SalonStatus.ACTIVE,
                    ),
                )
            )
            .annotate(
                rating=Avg("appointments__review__rating"),
                name=Concat(
                    "user__first_name",
                    Value(" "),
                    "user__last_name",
                ),
                popularity=Count(
                    "appointments",
                    filter=Q(appointments__status="completed"),
                    distinct=True,
                ),
            )
            .distinct()
        )


class WorkingScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = WorkingScheduleSerializer
    permission_classes = (IsMaster,)

    def get_queryset(self):
        return WorkingSchedule.objects.filter(master=self.request.user.master).order_by(
            "weekday", "start_time"
        )

    def perform_create(self, serializer):
        serializer.save(master=self.request.user.master)


class DayOffViewSet(viewsets.ModelViewSet):
    serializer_class = DayOffSerializer
    permission_classes = (IsMaster,)

    def get_queryset(self):
        return DayOff.objects.filter(master=self.request.user.master).order_by(
            "start_date"
        )

    def perform_create(self, serializer):
        serializer.save(master=self.request.user.master)


class ManageWorkingScheduleView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WorkingScheduleSerializer
    permission_classes = (IsMaster,)

    def get_queryset(self):
        return WorkingSchedule.objects.filter(master=self.request.user.master)


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if not request.user.has_usable_password():
            raise ValidationError(
                {"detail": "Password has not been set. Use the set-password endpoint."}
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class SetPasswordView(generics.GenericAPIView):
    serializer_class = SetPasswordSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if request.user.has_usable_password():
            raise ValidationError(
                {
                    "detail": (
                        "Password has already been set. "
                        "Use the change-password endpoint."
                    )
                }
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class VerifyEmailView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64 = serializer.validated_data["id"]
        token = serializer.validated_data["token"]

        UserAuthService.verify_email(uidb64, token)

        return Response(
            {"detail": "Email verified successfully."},
            status=status.HTTP_200_OK,
        )


class GoogleLoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = UserAuthService.authenticate_google_user(
            google_token=serializer.validated_data["id_token"],
        )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


class GoogleTestView(View):
    def get(self, request):
        return render(request, "test-google/test-google.html")
