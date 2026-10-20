"""
API views for the accounts app.
"""
from __future__ import annotations

from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts import services
from accounts.models import SubAdminPermission, User, UserRole
from accounts.permissions import IsAdmin, IsAdminOrSubAdmin
from accounts.serializers import (
    AdminUserUpdateSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    SubAdminPermissionSerializer,
    UserBasicSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class LoginThrottle(AnonRateThrottle):
    rate = "5/minute"
    scope = "login"


@extend_schema(tags=["auth"])
class LoginView(TokenObtainPairView):
    throttle_classes = [LoginThrottle]


@extend_schema(tags=["auth"])
class RefreshView(TokenRefreshView):
    pass


@extend_schema(tags=["auth"])
class LogoutView(APIView):
    """Blacklist the refresh token to log the user out."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass  # already blacklisted or invalid — still return 200
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)


@extend_schema(tags=["auth"])
class MeView(APIView):
    """Return the current authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    def patch(self, request: Request) -> Response:
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user, context={"request": request}).data)


@extend_schema(tags=["auth"])
class ChangePasswordView(APIView):
    """Change the authenticated user's own password."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully."})


@extend_schema(tags=["auth"])
class ForgotPasswordView(APIView):
    """Send a password-reset email (unauthenticated)."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request: Request) -> Response:
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.initiate_password_reset(serializer.validated_data["email"])
        # Always return 200 to prevent user enumeration
        return Response({"detail": "If that email is registered, a reset link has been sent."})


@extend_schema(tags=["auth"])
class ResetPasswordView(APIView):
    """Consume the one-time reset token and set a new password."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password reset successfully."})


# ── User management (Admin only) ──────────────────────────────────────────────

@extend_schema(tags=["users"])
class UserListCreateView(generics.ListCreateAPIView):
    """List all users or create a new one. Admin only."""

    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ["role", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["date_joined", "last_name", "email"]
    ordering = ["last_name"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        return User.objects.select_related("managed_department").all()

    def perform_create(self, serializer):
        user = services.create_user(**serializer.validated_data)
        self.created_user = user

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            UserSerializer(self.created_user, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["users"])
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or deactivate a user. Admin only."""

    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = User.objects.select_related("managed_department").all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return AdminUserUpdateSerializer
        return UserSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        services.deactivate_user(user)
        return Response({"detail": "User deactivated."}, status=status.HTTP_200_OK)


@extend_schema(tags=["users"])
class UnlockUserView(APIView):
    """Manually unlock a locked account. Admin only."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request: Request, pk: int) -> Response:
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        services.unlock_user(user)
        return Response({"detail": "Account unlocked."})


# ── Sub Admin permission matrix ───────────────────────────────────────────────

@extend_schema(tags=["permissions"])
class SubAdminPermissionListView(generics.ListCreateAPIView):
    """List or create Sub Admin module permissions. Admin only."""

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = SubAdminPermissionSerializer

    def get_queryset(self):
        return SubAdminPermission.objects.select_related("user").filter(
            user__role=UserRole.SUB_ADMIN
        )


@extend_schema(tags=["permissions"])
class SubAdminPermissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a Sub Admin permission. Admin only."""

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = SubAdminPermissionSerializer
    queryset = SubAdminPermission.objects.select_related("user").all()


@extend_schema(tags=["permissions"])
class UserPermissionMatrixView(APIView):
    """Get or replace the full permission matrix for a specific Sub Admin. Admin only."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request: Request, pk: int) -> Response:
        try:
            user = User.objects.get(pk=pk, role=UserRole.SUB_ADMIN)
        except User.DoesNotExist:
            return Response({"detail": "Sub Admin not found."}, status=status.HTTP_404_NOT_FOUND)
        matrix = services.get_subadmin_permissions(user)
        return Response({"user_id": pk, "permissions": matrix})

    def put(self, request: Request, pk: int) -> Response:
        try:
            user = User.objects.get(pk=pk, role=UserRole.SUB_ADMIN)
        except User.DoesNotExist:
            return Response({"detail": "Sub Admin not found."}, status=status.HTTP_404_NOT_FOUND)
        permissions = request.data.get("permissions", [])
        services.set_subadmin_permissions(user, permissions)
        return Response({"detail": "Permissions updated."})
