"""Leave business logic — approval workflow and balance management."""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from audit.middleware import get_current_actor, get_client_ip, get_current_request
from audit.services import log_action
from leave.models import LeaveBalance, LeaveRequest, LeaveStatus, LeaveType
from notifications.services import notify


def calculate_leave_allocation(years_of_service: float) -> Decimal:
    """Compute annual leave days based on service length.

    Ethiopian rule: 16 days in year 1, +1 day per 2 additional years of service.

    Args:
        years_of_service: Fractional years the employee has worked.

    Returns:
        Allocated leave days as Decimal.
    """
    base = Decimal("16")
    extra = Decimal(int(years_of_service / 2))
    return base + extra


@transaction.atomic
def allocate_annual_leave(employee, year: int) -> LeaveBalance:
    """Allocate annual leave for an employee for a given year.

    Args:
        employee: Employee instance.
        year: Year to allocate for.

    Returns:
        LeaveBalance instance.
    """
    try:
        annual_type = LeaveType.objects.get(code="ANNUAL")
    except LeaveType.DoesNotExist:
        return None

    days = calculate_leave_allocation(employee.years_of_service)
    balance, created = LeaveBalance.objects.get_or_create(
        employee=employee,
        leave_type=annual_type,
        year=year,
        defaults={"allocated_days": days},
    )
    if not created:
        balance.allocated_days = days
        balance.save(update_fields=["allocated_days"])
    return balance


@transaction.atomic
def submit_leave_request(
    employee,
    leave_type: LeaveType,
    start_date,
    end_date,
    number_of_days: Decimal,
    reason: str = "",
    document=None,
) -> LeaveRequest:
    """Employee submits a leave request.

    Args:
        employee: Employee making the request.
        leave_type: LeaveType instance.
        start_date: First day of leave.
        end_date: Last day of leave.
        number_of_days: Working days being requested.
        reason: Optional reason.
        document: Optional supporting document.

    Returns:
        New LeaveRequest.
    """
    from django.utils import timezone
    year = start_date.year

    # Check balance for paid leave
    if leave_type.is_paid:
        balance = LeaveBalance.objects.filter(
            employee=employee, leave_type=leave_type, year=year
        ).first()
        if not balance or balance.remaining_days < number_of_days:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                {"detail": f"Insufficient {leave_type.name} balance. "
                           f"Available: {balance.remaining_days if balance else 0} days."}
            )

    request = LeaveRequest.objects.create(
        employee=employee,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        number_of_days=number_of_days,
        reason=reason,
        document=document,
        status=LeaveStatus.PENDING,
    )
    log_action(
        actor=get_current_actor(),
        action="CREATE",
        obj=request,
        new_value={"type": leave_type.name, "days": str(number_of_days)},
    )
    recipient = getattr(employee, "user_account", None)
    notify(
        recipient=recipient,
        message=f"Your {leave_type.name} request for {number_of_days} days has been submitted.",
        category="leave",
        related_object_id=request.pk,
    )
    return request


@transaction.atomic
def manager_approve_leave(request: LeaveRequest, manager, notes: str = "") -> LeaveRequest:
    """Manager approves a pending leave request.

    Args:
        request: LeaveRequest in PENDING status.
        manager: Manager User performing the approval.
        notes: Optional notes.

    Returns:
        Updated LeaveRequest.
    """
    if request.status != LeaveStatus.PENDING:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"detail": "Only PENDING requests can be manager-approved."})

    # Nobody approves their own leave
    if hasattr(manager, "employee") and manager.employee == request.employee:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"detail": "You cannot approve your own leave request."})

    request.status = LeaveStatus.MANAGER_APPROVED
    request.manager_approved_by = manager
    request.manager_approved_at = timezone.now()
    request.manager_notes = notes
    request.save(update_fields=["status", "manager_approved_by", "manager_approved_at", "manager_notes", "updated_at"])

    log_action(actor=manager, action="APPROVE", obj=request, new_value={"status": "MANAGER_APPROVED"})
    notify(
        recipient=getattr(request.employee, "user_account", None),
        message=f"Your {request.leave_type.name} request has been approved by your manager.",
        category="leave",
        related_object_id=request.pk,
    )
    return request


@transaction.atomic
def hr_approve_leave(request: LeaveRequest, hr_user, notes: str = "") -> LeaveRequest:
    """HR (Sub Admin) confirms a manager-approved leave and deducts the balance.

    Args:
        request: LeaveRequest in MANAGER_APPROVED status.
        hr_user: HR User performing the confirmation.
        notes: Optional notes.

    Returns:
        Updated LeaveRequest.
    """
    if request.status != LeaveStatus.MANAGER_APPROVED:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"detail": "Only MANAGER_APPROVED requests can be HR-confirmed."})

    if hasattr(hr_user, "employee") and hr_user.employee == request.employee:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"detail": "You cannot approve your own leave request."})

    request.status = LeaveStatus.APPROVED
    request.hr_approved_by = hr_user
    request.hr_approved_at = timezone.now()
    request.hr_notes = notes
    request.save(update_fields=["status", "hr_approved_by", "hr_approved_at", "hr_notes", "updated_at"])

    # Deduct balance
    if request.leave_type.is_paid:
        year = request.start_date.year
        LeaveBalance.objects.filter(
            employee=request.employee,
            leave_type=request.leave_type,
            year=year,
        ).update(used_days=models_f_used(request))

    log_action(actor=hr_user, action="APPROVE", obj=request, new_value={"status": "APPROVED"})
    notify(
        recipient=getattr(request.employee, "user_account", None),
        message=f"Your {request.leave_type.name} request is fully approved by HR.",
        category="leave",
        related_object_id=request.pk,
    )
    return request


def models_f_used(request: LeaveRequest):
    """Return updated used_days using F() expression."""
    from django.db.models import F
    # We update via a separate query
    LeaveBalance.objects.filter(
        employee=request.employee,
        leave_type=request.leave_type,
        year=request.start_date.year,
    ).update(used_days=F("used_days") + request.number_of_days)
    # Return current value (not used as F expr — update is done above)
    b = LeaveBalance.objects.get(
        employee=request.employee,
        leave_type=request.leave_type,
        year=request.start_date.year,
    )
    return b.used_days


@transaction.atomic
def reject_leave(request: LeaveRequest, actor, reason: str = "") -> LeaveRequest:
    """Reject a leave request at any stage.

    Args:
        request: LeaveRequest to reject.
        actor: User performing the rejection.
        reason: Rejection reason.

    Returns:
        Updated LeaveRequest.
    """
    if request.status in (LeaveStatus.APPROVED, LeaveStatus.CANCELLED):
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"detail": "Cannot reject an already approved or cancelled request."})

    if hasattr(actor, "employee") and actor.employee == request.employee:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"detail": "You cannot reject your own leave request."})

    request.status = LeaveStatus.REJECTED
    request.rejection_reason = reason
    request.save(update_fields=["status", "rejection_reason", "updated_at"])

    log_action(actor=actor, action="REJECT", obj=request, new_value={"status": "REJECTED", "reason": reason})
    notify(
        recipient=getattr(request.employee, "user_account", None),
        message=f"Your {request.leave_type.name} request has been rejected. Reason: {reason}",
        category="leave",
        related_object_id=request.pk,
    )
    return request


@transaction.atomic
def cancel_leave(request: LeaveRequest, actor) -> LeaveRequest:
    """Employee or HR cancels a leave request.

    Args:
        request: LeaveRequest to cancel.
        actor: User performing the cancellation.

    Returns:
        Updated LeaveRequest.
    """
    if request.status == LeaveStatus.APPROVED:
        # Restore balance
        if request.leave_type.is_paid:
            from django.db.models import F
            LeaveBalance.objects.filter(
                employee=request.employee,
                leave_type=request.leave_type,
                year=request.start_date.year,
            ).update(used_days=F("used_days") - request.number_of_days)

    request.status = LeaveStatus.CANCELLED
    request.save(update_fields=["status", "updated_at"])
    log_action(actor=actor, action="UPDATE", obj=request, new_value={"status": "CANCELLED"})
    return request
