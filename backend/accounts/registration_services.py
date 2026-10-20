"""Business logic for the self-registration approval workflow with email notifications."""
from __future__ import annotations
import logging
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone
from notifications.services import notify

logger = logging.getLogger(__name__)


@transaction.atomic
def submit_registration(*, first_name, last_name, email, phone_number="",
                        requested_role="EMPLOYEE", department=None, position=None,
                        message="", raw_password):
    """Create a pending RegistrationRequest, notify admins via email + in-app."""
    from accounts.models import RegistrationRequest, RegistrationStatus, User, UserRole
    from config.email_service import (
        send_registration_submitted, notify_admins_new_registration
    )

    req = RegistrationRequest.objects.create(
        first_name=first_name, last_name=last_name,
        email=email.lower().strip(), phone_number=phone_number,
        requested_role=requested_role, department=department, position=position,
        message=message, password=make_password(raw_password),
        status=RegistrationStatus.PENDING,
    )

    # Email the applicant
    send_registration_submitted(email, first_name, req.pk)

    # Email + in-app notify all Admins and Sub-Admins
    admins = User.objects.filter(role__in=[UserRole.ADMIN, UserRole.SUB_ADMIN], is_active=True)
    admin_emails = [u.email for u in admins if u.email]
    notify_admins_new_registration(
        admin_emails, f"{first_name} {last_name}", email, requested_role, req.pk
    )
    for admin in admins:
        notify(
            recipient=admin,
            message=f"New registration request from {first_name} {last_name} "
                    f"<{email}> requesting {requested_role} access.",
            category="registration", related_object_id=req.pk,
        )
    logger.info("Registration request submitted: %s", email)
    return req


@transaction.atomic
def approve_registration(request, reviewer):
    """Approve registration → create User account → send approval email."""
    from accounts.models import RegistrationRequest, RegistrationStatus, User
    from config.email_service import send_registration_approved

    if request.status != RegistrationStatus.PENDING:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"detail": f"Cannot approve a {request.status} request."})

    user = User(
        email=request.email, first_name=request.first_name,
        last_name=request.last_name, phone_number=request.phone_number,
        role=request.requested_role,
        managed_department=request.department if request.requested_role == "MANAGER" else None,
        must_change_password=True, is_active=True,
    )
    user.password = request.password  # already hashed
    user.save()

    # Auto-create employee profile if department/position provided
    if request.department or request.position:
        try:
            from employees.models import Employee
            import datetime
            emp = Employee.objects.create(
                employee_id=_next_employee_id(),
                first_name=request.first_name, last_name=request.last_name,
                department=request.department, position=request.position,
                hire_date=datetime.date.today(), status="ACTIVE",
            )
            user.employee = emp
            user.save(update_fields=["employee"])
        except Exception as e:
            logger.warning("Could not auto-create employee for %s: %s", request.email, e)

    request.status = RegistrationStatus.APPROVED
    request.reviewed_by = reviewer
    request.reviewed_at = timezone.now()
    request.created_user = user
    request.save(update_fields=["status", "reviewed_by", "reviewed_at", "created_user", "updated_at"])

    # Send approval email
    send_registration_approved(request.email, request.first_name, request.requested_role)

    # In-app notification
    notify(recipient=user,
           message=f"Welcome {user.first_name}! Your registration is approved. "
                   f"You can now log in. Please change your password on first login.",
           category="registration", related_object_id=request.pk)
    logger.info("Registration approved: %s → user #%s", request.email, user.pk)
    return request


@transaction.atomic
def reject_registration(request, reviewer, reason):
    """Reject registration → send rejection email."""
    from accounts.models import RegistrationRequest, RegistrationStatus
    from config.email_service import send_registration_rejected

    if request.status != RegistrationStatus.PENDING:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"detail": f"Cannot reject a {request.status} request."})

    request.status = RegistrationStatus.REJECTED
    request.reviewed_by = reviewer
    request.reviewed_at = timezone.now()
    request.rejection_reason = reason
    request.save(update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason", "updated_at"])

    send_registration_rejected(request.email, request.first_name, reason)
    logger.info("Registration rejected: %s. Reason: %s", request.email, reason)
    return request


def _next_employee_id():
    from employees.models import Employee
    last = Employee.objects.order_by("-id").first()
    n = (last.id + 1) if last else 1
    return f"EMP-{n:05d}"
