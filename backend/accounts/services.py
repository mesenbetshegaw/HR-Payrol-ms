"""
Business logic for the accounts app.

All functions are pure: they receive validated data and return model instances.
Views and serializers must not contain business logic.
"""
from __future__ import annotations

import logging
import secrets
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from accounts.models import PasswordResetToken, SubAdminPermission, User, UserRole

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_RESET_TOKEN_EXPIRY_HOURS = 2


# ── User CRUD ─────────────────────────────────────────────────────────────────

def create_user(
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = UserRole.EMPLOYEE,
    phone_number: str = "",
    must_change_password: bool = False,
    managed_department=None,
) -> User:
    """Create and persist a new user account.

    Args:
        email: Unique email address (login identifier).
        password: Plain-text password (will be hashed).
        first_name: User's first name.
        last_name: User's last name.
        role: One of UserRole choices (default EMPLOYEE).
        phone_number: Optional phone number.
        must_change_password: Force password change on next login.
        managed_department: Department FK for MANAGER role.

    Returns:
        Newly created User instance.
    """
    user = User.objects.create_user(
        email=email.lower().strip(),
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role,
        phone_number=phone_number,
        must_change_password=must_change_password,
        managed_department=managed_department,
    )
    logger.info("User created: %s (role=%s)", user.email, role)
    return user


def update_user(user: User, **fields) -> User:
    """Update allowed user fields.

    Args:
        user: User instance to update.
        **fields: Arbitrary field/value pairs to set.

    Returns:
        Updated User instance.
    """
    for field, value in fields.items():
        setattr(user, field, value)
    user.save()
    return user


def deactivate_user(user: User) -> User:
    """Soft-delete a user by setting is_active=False.

    Args:
        user: User to deactivate.

    Returns:
        Updated User instance.
    """
    user.is_active = False
    user.save(update_fields=["is_active"])
    return user


def unlock_user(user: User) -> User:
    """Manually unlock a locked account.

    Args:
        user: User to unlock.

    Returns:
        Updated User instance.
    """
    user.failed_login_attempts = 0
    user.lockout_until = None
    user.save(update_fields=["failed_login_attempts", "lockout_until"])
    return user


# ── Password management ───────────────────────────────────────────────────────

def change_password(user: User, new_password: str) -> User:
    """Change a user's password and clear the must_change_password flag.

    Args:
        user: User whose password to change.
        new_password: New plain-text password.

    Returns:
        Updated User instance.
    """
    user.set_password(new_password)
    user.must_change_password = False
    user.save(update_fields=["password", "must_change_password"])
    return user


def initiate_password_reset(email: str) -> None:
    """Send a password-reset email if the address is registered.

    Silently does nothing if the email doesn't exist (prevents user enumeration).

    Args:
        email: Email address to look up.
    """
    try:
        user = User.objects.get(email=email.lower().strip(), is_active=True)
    except User.DoesNotExist:
        return  # Silent — don't reveal whether email exists

    # Invalidate any existing unused tokens
    PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

    token_value = secrets.token_urlsafe(32)
    expiry = timezone.now() + timezone.timedelta(hours=_RESET_TOKEN_EXPIRY_HOURS)
    PasswordResetToken.objects.create(user=user, token=token_value, expires_at=expiry)

    reset_url = f"http://localhost:5173/reset-password?token={token_value}"
    
    # Try HTML email first
    from config.email_service import send_password_reset
    sent = send_password_reset(user.email, user.get_full_name(), reset_url)
    
    if not sent:
        # Fallback to plain email
        send_mail(
            subject="HR Payroll — Password Reset Request",
            message=f"Hello {user.get_full_name()},\n\nReset link: {reset_url}\n\nExpires in {_RESET_TOKEN_EXPIRY_HOURS} hours.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    logger.info("Password reset initiated for: %s", user.email)


# ── Sub Admin permission matrix ───────────────────────────────────────────────

def set_subadmin_permissions(user: User, permissions: list[dict]) -> list[SubAdminPermission]:
    """Replace the full permission matrix for a Sub Admin user.

    Args:
        user: Sub Admin User instance.
        permissions: List of dicts with keys: module, can_view, can_create,
                     can_edit, can_delete, can_approve.

    Returns:
        List of created/updated SubAdminPermission instances.
    """
    if user.role != UserRole.SUB_ADMIN:
        raise ValueError("Permission matrix only applies to Sub Admin users.")

    results: list[SubAdminPermission] = []
    for perm_data in permissions:
        obj, _ = SubAdminPermission.objects.update_or_create(
            user=user,
            module=perm_data["module"],
            defaults={
                "can_view": perm_data.get("can_view", True),
                "can_create": perm_data.get("can_create", False),
                "can_edit": perm_data.get("can_edit", False),
                "can_delete": perm_data.get("can_delete", False),
                "can_approve": perm_data.get("can_approve", False),
            },
        )
        results.append(obj)
    return results


def get_subadmin_permissions(user: User) -> dict[str, dict]:
    """Return the permission matrix for a Sub Admin as a dict keyed by module.

    Args:
        user: Sub Admin User instance.

    Returns:
        Dict mapping module name → permissions dict.
    """
    perms = SubAdminPermission.objects.filter(user=user)
    return {
        p.module: {
            "can_view": p.can_view,
            "can_create": p.can_create,
            "can_edit": p.can_edit,
            "can_delete": p.can_delete,
            "can_approve": p.can_approve,
        }
        for p in perms
    }
