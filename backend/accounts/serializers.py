"""
Serializers for the accounts app.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.models import PasswordResetToken, SubAdminPermission, User, UserRole


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extend the default JWT obtain pair to:
    - check for account lockout before issuing tokens
    - reset failed-login counter on success
    - record failed attempts on failure
    """

    def validate(self, attrs: dict) -> dict:
        from django.conf import settings as s

        email = attrs.get(self.username_field, "").lower().strip()

        # Pre-check: does the user exist and is the account locked?
        try:
            user = User.objects.get(email=email)
            if user.is_locked:
                raise serializers.ValidationError(
                    "Account is temporarily locked due to too many failed login attempts. "
                    "Please try again later."
                )
        except User.DoesNotExist:
            pass  # Let the parent handle the invalid-credentials error

        try:
            data = super().validate(attrs)
        except Exception:
            # Record failed attempt
            try:
                u = User.objects.get(email=email)
                u.record_failed_login(
                    max_attempts=getattr(s, "ACCOUNT_LOCKOUT_ATTEMPTS", 5),
                    lockout_minutes=getattr(s, "ACCOUNT_LOCKOUT_MINUTES", 30),
                )
            except User.DoesNotExist:
                pass
            raise

        # Success: reset counter
        self.user.reset_failed_login()
        self.user.last_login = timezone.now()
        self.user.save(update_fields=["last_login"])

        # Add extra claims
        data["user"] = UserBasicSerializer(self.user).data
        data["must_change_password"] = self.user.must_change_password
        return data

    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        token["full_name"] = user.get_full_name()
        return token


class UserBasicSerializer(serializers.ModelSerializer):
    """Minimal user info included in JWT response."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name", "role", "profile_picture"]
        read_only_fields = fields

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name()


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer (Admin / Sub Admin views)."""

    full_name = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "phone_number",
            "profile_picture",
            "is_active",
            "is_locked",
            "must_change_password",
            "date_joined",
            "last_login",
            "managed_department",
        ]
        read_only_fields = ["id", "date_joined", "last_login", "is_locked"]

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name()

    def get_is_locked(self, obj: User) -> bool:
        return obj.is_locked


class UserCreateSerializer(serializers.ModelSerializer):
    """Create a new user account (Admin only)."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "role",
            "phone_number",
            "password",
            "confirm_password",
            "must_change_password",
            "managed_department",
        ]

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Update user account — Admin can change role; users update own profile."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "profile_picture",
            "managed_department",
        ]


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Admin-level user update including role and status."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "profile_picture",
            "role",
            "is_active",
            "must_change_password",
            "managed_department",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Change own password (authenticated user)."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["confirm_new_password"]:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match."})
        return attrs

    def save(self) -> None:
        user: User = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])


class ForgotPasswordSerializer(serializers.Serializer):
    """Request a password-reset email."""

    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    """Consume the one-time token and set a new password."""

    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["confirm_new_password"]:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match."})
        try:
            reset_token = PasswordResetToken.objects.select_related("user").get(
                token=attrs["token"]
            )
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid or expired token."})
        if not reset_token.is_valid:
            raise serializers.ValidationError({"token": "Token has expired or already been used."})
        attrs["reset_token"] = reset_token
        return attrs

    def save(self) -> None:
        reset_token: PasswordResetToken = self.validated_data["reset_token"]
        user: User = reset_token.user
        user.set_password(self.validated_data["new_password"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        reset_token.used = True
        reset_token.save(update_fields=["used"])


class SubAdminPermissionSerializer(serializers.ModelSerializer):
    """CRUD for the Sub Admin permission matrix."""

    class Meta:
        model = SubAdminPermission
        fields = [
            "id",
            "user",
            "module",
            "can_view",
            "can_create",
            "can_edit",
            "can_delete",
            "can_approve",
        ]

    def validate_user(self, value: User) -> User:
        if value.role != UserRole.SUB_ADMIN:
            raise serializers.ValidationError("Permissions matrix only applies to Sub Admin users.")
        return value
