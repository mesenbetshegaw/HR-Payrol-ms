"""
Custom User model, RBAC permission matrix, and self-registration workflow.
"""
from __future__ import annotations
import logging
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class UserRole(models.TextChoices):
    ADMIN     = "ADMIN",     "Admin"
    SUB_ADMIN = "SUB_ADMIN", "Sub Admin"
    MANAGER   = "MANAGER",   "Manager"
    EMPLOYEE  = "EMPLOYEE",  "Employee"


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        extra.setdefault("role", UserRole.EMPLOYEE)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", UserRole.ADMIN)
        return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    email          = models.EmailField(unique=True, db_index=True)
    first_name     = models.CharField(max_length=100)
    last_name      = models.CharField(max_length=100)
    role           = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.EMPLOYEE)
    is_active      = models.BooleanField(default=True)
    is_staff       = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    lockout_until  = models.DateTimeField(null=True, blank=True)
    must_change_password = models.BooleanField(default=False)
    date_joined    = models.DateTimeField(default=timezone.now)
    last_login     = models.DateTimeField(null=True, blank=True)
    profile_picture = models.FileField(upload_to="profiles/", null=True, blank=True)
    phone_number   = models.CharField(max_length=20, blank=True)
    employee       = models.OneToOneField(
        "employees.Employee", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="user_account"
    )
    managed_department = models.ForeignKey(
        "organization.Department", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="managers"
    )

    objects = UserManager()
    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_locked(self):
        return bool(self.lockout_until and timezone.now() < self.lockout_until)

    def record_failed_login(self, max_attempts=5, lockout_minutes=30):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.lockout_until = timezone.now() + timezone.timedelta(minutes=lockout_minutes)
            logger.warning("Account locked: %s", self.email)
        self.save(update_fields=["failed_login_attempts", "lockout_until"])

    def reset_failed_login(self):
        if self.failed_login_attempts or self.lockout_until:
            self.failed_login_attempts = 0
            self.lockout_until = None
            self.save(update_fields=["failed_login_attempts", "lockout_until"])


class PermissionModule(models.TextChoices):
    EMPLOYEES     = "employees",     "Employees"
    ATTENDANCE    = "attendance",    "Attendance"
    LEAVE         = "leave",         "Leave"
    PAYROLL       = "payroll",       "Payroll"
    REPORTS       = "reports",       "Reports"
    ORGANIZATION  = "organization",  "Organization"
    NOTIFICATIONS = "notifications", "Notifications"
    AUDIT         = "audit",         "Audit"


class SubAdminPermission(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sub_admin_permissions",
                                   limit_choices_to={"role": UserRole.SUB_ADMIN})
    module     = models.CharField(max_length=30, choices=PermissionModule.choices)
    can_view   = models.BooleanField(default=True)
    can_create = models.BooleanField(default=False)
    can_edit   = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_approve= models.BooleanField(default=False)

    class Meta:
        unique_together = [("user", "module")]

    def __str__(self):
        return f"{self.user.email} – {self.module}"


class PasswordResetToken(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token      = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used       = models.BooleanField(default=False)

    def __str__(self):
        return f"Reset token for {self.user.email}"

    @property
    def is_valid(self):
        return not self.used and timezone.now() <= self.expires_at


# ── Self-Registration Request ─────────────────────────────────────────────────

class RegistrationStatus(models.TextChoices):
    PENDING  = "PENDING",  "Pending Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class RegistrationRequest(models.Model):
    """
    Anyone can submit a self-registration request.
    Admins/Sub-Admins review and approve or reject it.
    On approval a User account is automatically created.
    """
    first_name     = models.CharField(max_length=100)
    last_name      = models.CharField(max_length=100)
    email          = models.EmailField(unique=True, db_index=True)
    phone_number   = models.CharField(max_length=20, blank=True)
    requested_role = models.CharField(
        max_length=20,
        choices=[("EMPLOYEE","Employee"),("MANAGER","Manager"),("SUB_ADMIN","Sub Admin")],
        default="EMPLOYEE",
    )
    department = models.ForeignKey(
        "organization.Department", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="registration_requests"
    )
    position = models.ForeignKey(
        "organization.Position", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="registration_requests"
    )
    message       = models.TextField(blank=True)
    password      = models.CharField(max_length=128)   # hashed on save

    status        = models.CharField(max_length=20, choices=RegistrationStatus.choices,
                                     default=RegistrationStatus.PENDING, db_index=True)
    reviewed_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name="reviewed_registrations")
    reviewed_at   = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_user  = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name="registration_request")

    submitted_at  = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}> [{self.status}]"
