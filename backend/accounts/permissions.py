"""
DRF permission classes implementing role-based access control.

Usage in views:
    permission_classes = [IsAuthenticated, IsAdminUser]
    permission_classes = [IsAuthenticated, IsSubAdminWithPermission("payroll", "can_approve")]
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from accounts.models import UserRole


class IsAdmin(BasePermission):
    """Full access: Admin role only."""

    message = "Only system administrators can perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.ADMIN)


class IsSubAdmin(BasePermission):
    """Sub Admin role only (no granular check)."""

    message = "Only HR/Payroll officers can perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN)
        )


class IsManager(BasePermission):
    """Manager role only."""

    message = "Only department managers can perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN, UserRole.MANAGER)
        )


class IsAdminOrSubAdmin(BasePermission):
    """Admin or Sub Admin."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN)
        )


class IsOwnProfile(BasePermission):
    """
    Object-level: the requester can only access their own object
    unless they are Admin or Sub Admin.
    """

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if request.user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN):
            return True
        # obj might be a User or an Employee
        if hasattr(obj, "user_account"):
            return obj.user_account == request.user
        return obj == request.user


def make_subadmin_permission(module: str, action: str = "can_view"):
    """
    Factory that returns a DRF permission class checking the Sub Admin
    permission matrix for (module, action).

    Example:
        permission_classes = [IsAuthenticated, make_subadmin_permission("payroll", "can_approve")]
    """

    class SubAdminModulePermission(BasePermission):
        message = f"You don't have '{action}' permission on module '{module}'."

        def has_permission(self, request: Request, view: APIView) -> bool:
            user = request.user
            if not user or not user.is_authenticated:
                return False
            if user.role == UserRole.ADMIN:
                return True
            if user.role != UserRole.SUB_ADMIN:
                return False
            return user.sub_admin_permissions.filter(
                module=module,
                **{action: True},
            ).exists()

    SubAdminModulePermission.__name__ = f"SubAdmin_{module}_{action}"
    return SubAdminModulePermission


class IsSameDepartment(BasePermission):
    """
    Object-level: Manager can only access employees in their own department.
    Admin and Sub Admin bypass this.
    """

    message = "You can only access members of your own department."

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        user = request.user
        if user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN):
            return True
        if user.role == UserRole.MANAGER:
            # obj should have a department attribute
            employee_dept = getattr(obj, "department", None)
            return employee_dept is not None and employee_dept == user.managed_department
        # Employee: own record only
        if hasattr(obj, "user_account"):
            return obj.user_account == user
        return obj == user
