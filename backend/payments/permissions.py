from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS
)


class IsAdminOrAuthenticatedReadOnly(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user.is_authenticated:
            return False

        return (
                request.user.is_staff
                or request.method in SAFE_METHODS
        )
