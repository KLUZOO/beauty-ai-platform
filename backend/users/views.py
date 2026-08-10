from beauty_service.models import Service
from django.db.models import Avg, Count, F, Prefetch, Q, Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404, render
from django.views import View
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import generics, serializers, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from salons.models import Salon, SalonStatus

from users.models import DayOff, FavoriteMaster, Master, MasterStatus, WorkingSchedule
from users.permissions import IsMaster
from users.serializers import (
    ChangePasswordSerializer,
    DayOffSerializer,
    FavoriteMasterSerializer,
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


class FavoriteMastersListView(generics.ListAPIView):
    serializer_class = FavoriteMasterSerializer
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Get favorite masters",
        description=(
            "Returns the authenticated client's list of favorite masters. "
            "Only active masters are included."
        ),
        responses={
            200: FavoriteMasterSerializer(many=True),
            401: OpenApiResponse(
                description="Authentication credentials were not provided "
                "or are invalid.",
            ),
        },
        tags=["Favorite Masters"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Master.objects.filter(
                favorite_relations__client=self.request.user,
                account_status=MasterStatus.ACTIVE,
            )
            .annotate(
                rating=Avg(
                    "appointments__review__rating",
                ),
                favorite_created_at=F(
                    "favorite_relations__created_at",
                ),
            )
            .select_related("user")
            .prefetch_related(
                "salons",
                Prefetch(
                    "services",
                    queryset=Service.objects.filter(is_active=True),
                    to_attr="active_services_list",
                ),
            )
            .distinct()
        )


class FavoriteMasterView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Add master to favorites",
        description=(
            "Adds an active master to the authenticated client's "
            "favorite masters list. A master can only be added once."
        ),
        parameters=[
            OpenApiParameter(
                name="master_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the master to add to favorites.",
                required=True,
            ),
        ],
        responses={
            201: FavoriteMasterSerializer,
            400: OpenApiResponse(
                description="The master is already in favorites.",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided "
                "or are invalid.",
            ),
            404: OpenApiResponse(
                description="Master not found or master is not active.",
            ),
        },
        tags=["Favorite Masters"],
    )
    def post(self, request, master_id):
        master = get_object_or_404(
            Master.objects.filter(
                account_status=MasterStatus.ACTIVE,
            )
            .annotate(
                rating=Avg(
                    "appointments__review__rating",
                ),
                favorite_created_at=F(
                    "favorite_relations__created_at",
                ),
            )
            .select_related("user")
            .prefetch_related(
                Prefetch(
                    "salons",
                    queryset=Salon.objects.filter(
                        salon_status=SalonStatus.ACTIVE,
                    ),
                )
            ),
            id=master_id,
        )

        favorite, created = FavoriteMaster.objects.get_or_create(
            client=request.user,
            master=master,
        )

        if not created:
            return Response(
                {"detail": "Master is already in favorites."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        master.favorite_created_at = favorite.created_at

        serializer = FavoriteMasterSerializer(master)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Remove master from favorites",
        description=(
            "Removes the specified master from the authenticated client's "
            "favorite masters list. This does not affect appointment history."
        ),
        parameters=[
            OpenApiParameter(
                name="master_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the master to remove from favorites.",
                required=True,
            ),
        ],
        responses={
            204: OpenApiResponse(
                description="Master successfully removed from favorites.",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided "
                "or are invalid.",
            ),
            404: OpenApiResponse(
                description="The master is not in the authenticated client's "
                "favorites.",
            ),
        },
        tags=["Favorite Masters"],
    )
    def delete(self, request, master_id):
        favorite = get_object_or_404(
            FavoriteMaster,
            client=request.user,
            master_id=master_id,
        )

        favorite.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Check if master is in favorites",
        description=(
            "Returns whether the specified master is in the "
            "authenticated client's favorites."
        ),
        parameters=[
            OpenApiParameter(
                name="master_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the master.",
                required=True,
            ),
        ],
        responses={
            200: inline_serializer(
                name="FavoriteMasterStatus",
                fields={
                    "is_favorite": serializers.BooleanField(),
                },
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided "
                "or are invalid.",
            ),
        },
        tags=["Favorite Masters"],
    )
    def get(self, request, master_id):
        is_favorite = FavoriteMaster.objects.filter(
            client=request.user,
            master_id=master_id,
        ).exists()

        return Response(
            {"is_favorite": is_favorite},
            status=status.HTTP_200_OK,
        )
