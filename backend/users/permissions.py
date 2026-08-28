from rest_framework.permissions import (
    BasePermission,
)

from users.models import MasterStatus


class IsMaster(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_master
            and request.user.master.account_status == MasterStatus.ACTIVE
        )
