"""
Self-registration request model.

Flow:
  1. Anyone visits /register and fills the form → RegistrationRequest created (PENDING)
  2. All Admins and Sub-Admins receive in-app notification
  3. Any Admin/Sub-Admin opens the request and APPROVES or REJECTS it
  4. On APPROVE → User account is created automatically, welcome notification sent
  5. On REJECT  → Rejection reason sent back, request marked REJECTED
"""
from django.db import models
from django.utils import timezone


class RegistrationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class RegistrationRequest(models.Model):
    """A self-service registration request awaiting admin approval."""

    # Personal info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)

    # Desired role (Employee or Manager — Admin cannot self-register)
    requested_role = models.CharField(
        max_length=20,
        choices=[("EMPLOYEE", "Employee"), ("MANAGER", "Manager"), ("SUB_ADMIN", "Sub Admin")],
        default="EMPLOYEE",
    )

    # Employment info provided at registration
    department = models.ForeignKey(
        "organization.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registration_requests",
    )
    position = models.ForeignKey(
        "organization.Position",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registration_requests",
    )
    message = models.TextField(
        blank=True,
        help_text="Applicant's message / reason for joining",
    )

    # Desired password (stored hashed after approval)
    password = models.CharField(max_length=128)  # will be hashed before save

    # Workflow
    status = models.CharField(
        max_length=20,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_registrations",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Resulting user (set on approval)
    created_user = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registration_request",
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Registration Request"
        verbose_name_plural = "Registration Requests"

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}> [{self.status}]"
