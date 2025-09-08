# preorder/permissions.py
from rest_framework.permissions import BasePermission

class IsOpsManager(BasePermission):
    """
    Allows access only to Ops Managers.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "ops_manager"
        )


class IsCustomer(BasePermission):
    """
    Allows access only to Customers.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "customer"
        )
