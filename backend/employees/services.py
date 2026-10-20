"""Employee business logic."""
from __future__ import annotations

import csv
import io
from typing import Any

from django.db import transaction

from audit.middleware import get_current_actor, get_client_ip, get_current_request
from audit.services import log_action
from employees.models import Employee, EmployeeStatusHistory, EmploymentStatus


def generate_employee_id() -> str:
    """Generate next sequential employee ID like EMP-00042."""
    last = Employee.objects.order_by("-id").first()
    next_num = (last.id + 1) if last else 1
    return f"EMP-{next_num:05d}"


@transaction.atomic
def create_employee(data: dict) -> Employee:
    """Create a new employee record.

    Args:
        data: Validated field data for Employee model.

    Returns:
        New Employee instance.
    """
    data.setdefault("employee_id", generate_employee_id())
    employee = Employee.objects.create(**data)
    log_action(
        actor=get_current_actor(),
        action="CREATE",
        obj=employee,
        new_value={"employee_id": employee.employee_id, "name": employee.get_full_name()},
        ip_address=get_client_ip(get_current_request()) if get_current_request() else None,
    )
    return employee


@transaction.atomic
def update_employee(employee: Employee, data: dict) -> Employee:
    """Update employee fields.

    Args:
        employee: Employee instance to update.
        data: Dict of field/value pairs.

    Returns:
        Updated Employee instance.
    """
    old = {"status": employee.status, "department_id": employee.department_id}
    for field, value in data.items():
        setattr(employee, field, value)
    employee.save()
    log_action(
        actor=get_current_actor(),
        action="UPDATE",
        obj=employee,
        old_value=old,
        new_value=data,
        ip_address=get_client_ip(get_current_request()) if get_current_request() else None,
    )
    return employee


@transaction.atomic
def change_employee_status(
    employee: Employee, new_status: str, reason: str = "", changed_by=None
) -> Employee:
    """Change employee employment status and write history.

    Args:
        employee: Target employee.
        new_status: One of EmploymentStatus choices.
        reason: Human-readable reason for the change.
        changed_by: User performing the change.

    Returns:
        Updated Employee instance.
    """
    old_status = employee.status
    employee.status = new_status
    employee.save(update_fields=["status", "updated_at"])
    EmployeeStatusHistory.objects.create(
        employee=employee,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by or get_current_actor(),
        reason=reason,
    )
    log_action(
        actor=get_current_actor(),
        action="UPDATE",
        obj=employee,
        old_value={"status": old_status},
        new_value={"status": new_status, "reason": reason},
    )
    return employee


def export_employees_csv(queryset) -> str:
    """Export a queryset of employees to CSV string.

    Args:
        queryset: Employee queryset.

    Returns:
        CSV content as string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Employee ID", "First Name", "Last Name", "Department",
        "Position", "Status", "Hire Date", "TIN", "Phone",
    ])
    for emp in queryset.select_related("department", "position"):
        writer.writerow([
            emp.employee_id, emp.first_name, emp.last_name,
            emp.department.name if emp.department else "",
            emp.position.name if emp.position else "",
            emp.status, emp.hire_date, emp.tin_number, emp.phone_number,
        ])
    return output.getvalue()
