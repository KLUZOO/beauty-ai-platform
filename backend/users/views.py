from beauty_service.models import Service
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import Avg, Count, F, Prefetch, Q, QuerySet, Sum, Value
from django.db.models.functions import Concat
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import generics, mixins, serializers, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from salons.models import Salon, SalonStatus

from users.filters import UsersFilter
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


@extend_schema(
    summary="Register a new user",
    description="Creates a new user account with email and password.",
    tags=["Authentication & Registration"],
    responses={
        201: UserSerializer,
        400: OpenApiResponse(
            description="Validation error (e.g., email already exists)."
        ),
    },
)
class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve user profile",
        description="Returns detailed profile information for the authenticated user.",
        tags=["User Profile"],
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid."
            ),
        },
    ),
    put=extend_schema(
        summary="Update user profile",
        description="Updates all fields of the authenticated user's profile.",
        tags=["User Profile"],
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid."
            ),
        },
    ),
    patch=extend_schema(
        summary="Partially update user profile",
        description="Updates specific fields of the authenticated user's profile.",
        tags=["User Profile"],
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description="Validation error."),
            401: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid."
            ),
        },
    ),
)
class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = (
            get_user_model()
            .objects.filter(master__isnull=True)
            .annotate(
                bookings_count=Count(
                    "appointments",
                    filter=Q(appointments__status__in=["confirmed", "completed"]),
                    distinct=True,
                ),
                total_spent=Sum(
                    "appointments__payments__amount",
                    filter=Q(appointments__status__in=["confirmed", "completed"])
                    & Q(
                        appointments__payments__payment_status="completed",
                    ),
                ),
            )
        )
        return queryset

    def get_object(self) -> AbstractBaseUser:
        return self.get_queryset().get(pk=self.request.user.pk)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve master profile",
        description="Returns the master profile associated with the currently authenticated user.",
        tags=["Master Profile"],
        responses={
            200: MasterProfileSerializer,
            403: OpenApiResponse(
                description="Permission denied. Access is restricted to masters only."
            ),
        },
    ),
    put=extend_schema(
        summary="Update master profile",
        tags=["Master Profile"],
        responses={
            200: MasterProfileSerializer,
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(
                description="Permission denied. Access is restricted to masters only."
            ),
        },
    ),
    patch=extend_schema(
        summary="Partially update master profile",
        tags=["Master Profile"],
        responses={
            200: MasterProfileSerializer,
            400: OpenApiResponse(description="Validation error."),
            403: OpenApiResponse(
                description="Permission denied. Access is restricted to masters only."
            ),
        },
    ),
)
class ManageMasterView(generics.RetrieveUpdateAPIView):
    serializer_class = MasterProfileSerializer
    permission_classes = (IsMaster,)

    def get_object(self) -> str:
        return self.request.user.master


@extend_schema_view(
    list=extend_schema(
        summary="List clients",
        description=(
            "Returns a paginated list of clients. "
            "Clients are users without an associated master profile."
        ),
        tags=["Clients"],
        responses={
            200: UserProfileSerializer(many=True),
            401: OpenApiResponse(
                description="Authentication credentials were not provided "
                "or are invalid."
            ),
            403: OpenApiResponse(
                description="Access is restricted to staff/admin users."
            ),
        },
    ),
    retrieve=extend_schema(
        summary="Retrieve client",
        description="Returns detailed information about a specific client.",
        tags=["Clients"],
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(
                description="Authentication credentials were not provided "
                "or are invalid."
            ),
            403: OpenApiResponse(
                description="Access is restricted to staff/admin users."
            ),
            404: OpenApiResponse(description="Client not found."),
        },
    ),
)
class ClientListView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAdminUser,)

    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )

    filterset_class = UsersFilter

    ordering_fields = (
        "first_name",
        "last_name",
        "registration_date_user",
        "bookings_count",
        "total_spent",
    )

    ordering = ("-registration_date_user",)

    def get_queryset(self):
        queryset = (
            get_user_model()
            .objects.filter(master__isnull=True)
            .annotate(
                bookings_count=Count(
                    "appointments",
                    filter=Q(appointments__status__in=["confirmed", "completed"]),
                    distinct=True,
                ),
                total_spent=Sum(
                    "appointments__payments__amount",
                    filter=Q(appointments__status__in=["confirmed", "completed"])
                    & Q(
                        appointments__payments__payment_status="completed",
                    ),
                ),
            )
        )
        return queryset


@extend_schema(
    summary="List active masters",
    description="Returns a list of all active masters with optional ordering by rating, name, experience, or popularity.",
    tags=["Masters"],
    responses={
        200: MasterListSerializer(many=True),
        401: OpenApiResponse(
            description="Authentication credentials were not provided or are invalid."
        ),
    },
)
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

    def get_queryset(self) -> QuerySet:
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


@extend_schema_view(
    get=extend_schema(
        summary="Get working schedule",
        description="Retrieves the recurring weekly working schedule for the authenticated master.",
        tags=["Master Working Schedule"],
        responses={
            200: WorkingScheduleSerializer(many=True),
            403: OpenApiResponse(
                description="Permission denied. Access is restricted to masters only."
            ),
        },
    ),
    post=extend_schema(
        summary="Create working schedule entry",
        description="Creates a new working day schedule entry for the authenticated master.",
        tags=["Master Working Schedule"],
        responses={
            201: WorkingScheduleSerializer,
            400: OpenApiResponse(
                description="Validation error (e.g., overlapping working hours or invalid time sequence)."
            ),
            403: OpenApiResponse(
                description="Permission denied. Access is restricted to masters only."
            ),
        },
    ),
)
class WorkingScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = WorkingScheduleSerializer
    permission_classes = (IsMaster,)

    def get_queryset(self) -> QuerySet[WorkingSchedule]:
        return WorkingSchedule.objects.filter(master=self.request.user.master).order_by(
            "weekday", "start_time"
        )

    def perform_create(self, serializer) -> None:
        serializer.save(master=self.request.user.master)


@extend_schema_view(
    list=extend_schema(
        summary="List days off",
        description="Retrieves a list of scheduled days off/vacations for the authenticated master.",
        tags=["Master Days Off"],
        responses={200: DayOffSerializer(many=True)},
    ),
    create=extend_schema(
        summary="Create day off",
        description="Creates a new day off entry for the authenticated master.",
        tags=["Master Days Off"],
        responses={
            201: DayOffSerializer,
            400: OpenApiResponse(
                description="Validation error (e.g., date range overlaps or conflicts with confirmed appointments)."
            ),
        },
    ),
    retrieve=extend_schema(
        summary="Retrieve day off details",
        tags=["Master Days Off"],
        responses={
            200: DayOffSerializer,
            404: OpenApiResponse(description="Day off record not found."),
        },
    ),
    update=extend_schema(
        summary="Update day off",
        tags=["Master Days Off"],
        responses={
            200: DayOffSerializer,
            400: OpenApiResponse(description="Validation error."),
        },
    ),
    partial_update=extend_schema(
        summary="Partially update day off",
        tags=["Master Days Off"],
        responses={
            200: DayOffSerializer,
            400: OpenApiResponse(description="Validation error."),
        },
    ),
    destroy=extend_schema(
        summary="Delete day off",
        tags=["Master Days Off"],
        responses={
            204: OpenApiResponse(description="Day off record successfully deleted."),
        },
    ),
)
class DayOffViewSet(viewsets.ModelViewSet):
    serializer_class = DayOffSerializer
    permission_classes = (IsMaster,)

    def get_queryset(self) -> QuerySet[DayOff]:
        return DayOff.objects.filter(master=self.request.user.master).order_by(
            "start_date"
        )

    def perform_create(self, serializer) -> None:
        serializer.save(master=self.request.user.master)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve working schedule details",
        tags=["Master Working Schedule"],
        responses={
            200: WorkingScheduleSerializer,
            404: OpenApiResponse(description="Working schedule entry not found."),
        },
    ),
    put=extend_schema(
        summary="Update working schedule entry",
        tags=["Master Working Schedule"],
        responses={
            200: WorkingScheduleSerializer,
            400: OpenApiResponse(description="Validation error."),
        },
    ),
    patch=extend_schema(
        summary="Partially update working schedule entry",
        tags=["Master Working Schedule"],
        responses={
            200: WorkingScheduleSerializer,
            400: OpenApiResponse(description="Validation error."),
        },
    ),
    delete=extend_schema(
        summary="Delete working schedule entry",
        tags=["Master Working Schedule"],
        responses={
            204: OpenApiResponse(
                description="Working schedule entry successfully deleted."
            ),
        },
    ),
)
class ManageWorkingScheduleView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WorkingScheduleSerializer
    permission_classes = (IsMaster,)

    def get_queryset(self) -> QuerySet[WorkingSchedule, WorkingSchedule]:
        return WorkingSchedule.objects.filter(master=self.request.user.master)


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Change user password",
        description="Changes the password for the currently authenticated user. Requires old password verification.",
        tags=["Authentication & Registration"],
        responses={
            204: OpenApiResponse(description="Password changed successfully."),
            400: OpenApiResponse(
                description="Incorrect old password or new password validation error."
            ),
        },
    )
    def post(self, request) -> Response:
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

    @extend_schema(
        summary="Set user password",
        description="Sets a password for users who registered via OAuth (e.g., Google) and do not have a usable password yet.",
        tags=["Authentication & Registration"],
        responses={
            204: OpenApiResponse(description="Password set successfully."),
            400: OpenApiResponse(
                description="Password has already been set or invalid data provided."
            ),
        },
    )
    def post(self, request) -> Response:
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

    @extend_schema(
        summary="Verify email address",
        description="Verifies user email using the uidb64 and token received via email confirmation link.",
        request=VerifyEmailSerializer,
        tags=["Authentication & Registration"],
        responses={
            200: OpenApiResponse(description="Email verified successfully."),
            400: OpenApiResponse(description="Invalid token or user ID."),
        },
    )
    def post(self, request) -> Response:
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

    @extend_schema(
        summary="Google OAuth2 login",
        description="Authenticates a user via Google ID Token and returns a pair of JWT tokens (access and refresh).",
        request=GoogleLoginSerializer,
        tags=["Authentication & Registration"],
        responses={
            200: OpenApiResponse(
                description="Successfully authenticated. Returns JWT access and refresh tokens.",
            ),
            400: OpenApiResponse(description="Invalid Google token."),
        },
    )
    def post(self, request) -> Response:
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
    # noinspection PyMethodMayBeStatic
    def get(self, request) -> HttpResponse:
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
    def get(self, request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet:
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
    def post(self, request, master_id) -> Response:
        master = get_object_or_404(
            Master.objects.filter(
                account_status=MasterStatus.ACTIVE,
            )
            .annotate(
                rating=Avg(
                    "appointments__review__rating",
                ),
            )
            .select_related("user")
            .prefetch_related(
                Prefetch(
                    "salons",
                    queryset=Salon.objects.filter(
                        salon_status=SalonStatus.ACTIVE,
                    ),
                ),
                Prefetch(
                    "services",
                    queryset=Service.objects.filter(is_active=True),
                    to_attr="active_services_list",
                ),
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
    def delete(self, request, master_id) -> Response:
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
    def get(self, request, master_id) -> Response:
        is_favorite = FavoriteMaster.objects.filter(
            client=request.user,
            master_id=master_id,
        ).exists()

        return Response(
            {"is_favorite": is_favorite},
            status=status.HTTP_200_OK,
        )
