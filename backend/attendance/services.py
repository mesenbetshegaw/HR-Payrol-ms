"""Attendance business logic."""
from __future__ import annotations

import calendar
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from attendance.models import AttendanceRecord, AttendanceStatus, MonthlySummary, OvertimeStatus


@transaction.atomic
def check_in(employee_id: int, date, check_in_time, notes: str = "", is_manual: bool = False, actor=None) -> AttendanceRecord:
    """Record employee check-in.

    Args:
        employee_id: Employee PK.
        date: Date of attendance.
        check_in_time: Time of check-in.
        notes: Optional notes.
        is_manual: True if entered manually by HR.
        actor: User performing manual entry.

    Returns:
        Created or updated AttendanceRecord.
    """
    record, created = AttendanceRecord.objects.get_or_create(
        employee_id=employee_id,
        date=date,
        defaults={
            "check_in": check_in_time,
            "status": AttendanceStatus.PRESENT,
            "notes": notes,
            "is_manual": is_manual,
            "manual_entry_by": actor if is_manual else None,
        },
    )
    if not created:
        record.check_in = check_in_time
        record.is_manual = is_manual
        if actor:
            record.manual_entry_by = actor
        record.save(update_fields=["check_in", "is_manual", "manual_entry_by", "updated_at"])
    return record


@transaction.atomic
def check_out(record: AttendanceRecord, check_out_time, overtime_hours: Decimal = Decimal("0"), overtime_type: str = "") -> AttendanceRecord:
    """Record employee check-out and overtime.

    Args:
        record: Existing AttendanceRecord.
        check_out_time: Time of check-out.
        overtime_hours: Overtime hours logged.
        overtime_type: Category of overtime (NORMAL/NIGHT/REST/HOLIDAY).

    Returns:
        Updated AttendanceRecord.
    """
    record.check_out = check_out_time
    if overtime_hours > 0:
        record.overtime_hours = overtime_hours
        record.overtime_type = overtime_type
        record.overtime_status = OvertimeStatus.PENDING
    record.save(update_fields=["check_out", "overtime_hours", "overtime_type", "overtime_status", "updated_at"])
    return record


@transaction.atomic
def approve_overtime(record: AttendanceRecord, approved_by) -> AttendanceRecord:
    """Manager approves overtime for an attendance record.

    Args:
        record: AttendanceRecord with overtime.
        approved_by: Manager User.

    Returns:
        Updated AttendanceRecord.
    """
    record.overtime_status = OvertimeStatus.APPROVED
    record.overtime_approved_by = approved_by
    record.save(update_fields=["overtime_status", "overtime_approved_by", "updated_at"])
    return record


def compute_monthly_summary(employee_id: int, year: int, month: int) -> MonthlySummary:
    """Compute and store monthly attendance summary for an employee.

    Args:
        employee_id: Employee PK.
        year: Calendar year.
        month: Calendar month (1-12).

    Returns:
        Created or updated MonthlySummary.
    """
    records = AttendanceRecord.objects.filter(
        employee_id=employee_id,
        date__year=year,
        date__month=month,
    )
    summary, _ = MonthlySummary.objects.update_or_create(
        employee_id=employee_id,
        year=year,
        month=month,
        defaults={
            "present_days": records.filter(status=AttendanceStatus.PRESENT).count(),
            "absent_days": records.filter(status=AttendanceStatus.ABSENT).count(),
            "late_days": records.filter(status=AttendanceStatus.LATE).count(),
            "half_days": records.filter(status=AttendanceStatus.HALF_DAY).count(),
            "total_overtime_hours": sum(
                r.overtime_hours for r in records.filter(overtime_status=OvertimeStatus.APPROVED)
            ),
        },
    )
    return summary
