"""
Shared pytest fixtures for the HR Payroll test suite.
"""
import datetime
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import SubAdminPermission, User, UserRole, PermissionModule
from employees.models import Employee
from organization.models import Branch, Department, Position


# ── User fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        email="admin@test.et",
        password="Admin@1234",
        first_name="Admin",
        last_name="Test",
        role=UserRole.ADMIN,
        is_staff=True,
        is_superuser=True,
    )
    return user


@pytest.fixture
def subadmin_user(db):
    user = User.objects.create_user(
        email="subadmin@test.et",
        password="Sub@1234",
        first_name="Sub",
        last_name="Admin",
        role=UserRole.SUB_ADMIN,
    )
    # Grant all permissions
    for module in PermissionModule.values:
        SubAdminPermission.objects.create(
            user=user, module=module,
            can_view=True, can_create=True, can_edit=True, can_delete=True, can_approve=True,
        )
    return user


@pytest.fixture
def department(db):
    return Department.objects.create(name="Engineering", code="ENG")


@pytest.fixture
def position(db, department):
    return Position.objects.create(name="Engineer", department=department, grade="G3")


@pytest.fixture
def branch(db):
    return Branch.objects.create(name="HQ", city="Addis Ababa")


@pytest.fixture
def manager_user(db, department):
    user = User.objects.create_user(
        email="manager@test.et",
        password="Mgr@1234",
        first_name="Dept",
        last_name="Manager",
        role=UserRole.MANAGER,
        managed_department=department,
    )
    return user


@pytest.fixture
def employee_profile(db, department, position, branch):
    emp = Employee.objects.create(
        employee_id="EMP-TEST-001",
        first_name="Test",
        last_name="Employee",
        department=department,
        position=position,
        branch=branch,
        hire_date=datetime.date(2022, 1, 1),
        status="ACTIVE",
    )
    return emp


@pytest.fixture
def employee_user(db, employee_profile):
    user = User.objects.create_user(
        email="employee@test.et",
        password="Emp@1234",
        first_name="Test",
        last_name="Employee",
        role=UserRole.EMPLOYEE,
        employee=employee_profile,
    )
    return user


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def subadmin_client(api_client, subadmin_user):
    api_client.force_authenticate(user=subadmin_user)
    return api_client


@pytest.fixture
def manager_client(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    return api_client


@pytest.fixture
def employee_client(api_client, employee_user):
    api_client.force_authenticate(user=employee_user)
    return api_client


# ── Payroll fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def tax_brackets(db):
    from payroll.models import TaxBracket
    TaxBracket.objects.all().delete()
    brackets = [
        (Decimal("0"), Decimal("2000"), Decimal("0"), Decimal("0")),
        (Decimal("2001"), Decimal("4000"), Decimal("0.15"), Decimal("300")),
        (Decimal("4001"), Decimal("7000"), Decimal("0.20"), Decimal("500")),
        (Decimal("7001"), Decimal("10000"), Decimal("0.25"), Decimal("850")),
        (Decimal("10001"), Decimal("14000"), Decimal("0.30"), Decimal("1350")),
        (Decimal("14001"), None, Decimal("0.35"), Decimal("2050")),
    ]
    for min_i, max_i, rate, ded in brackets:
        TaxBracket.objects.create(min_income=min_i, max_income=max_i, rate=rate, deduction=ded)


@pytest.fixture
def pension_setting(db):
    from payroll.models import PensionSetting
    return PensionSetting.objects.create(
        employee_rate=Decimal("0.07"),
        employer_rate=Decimal("0.11"),
        pension_reduces_taxable_income=False,
        effective_date=datetime.date(2020, 1, 1),
    )


@pytest.fixture
def salary_structure(db, employee_profile):
    from payroll.models import SalaryStructure
    return SalaryStructure.objects.create(
        employee=employee_profile,
        basic_salary=Decimal("10000"),
        housing_allowance=Decimal("0"),
        transport_allowance=Decimal("0"),
        non_taxable_allowance=Decimal("0"),
        effective_date=datetime.date(2022, 1, 1),
    )


# ── Leave fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def leave_type_annual(db):
    from leave.models import LeaveType
    return LeaveType.objects.create(
        name="Annual Leave", code="ANNUAL", default_days_per_year=16, is_paid=True
    )


@pytest.fixture
def leave_balance(db, employee_profile, leave_type_annual):
    from leave.models import LeaveBalance
    return LeaveBalance.objects.create(
        employee=employee_profile,
        leave_type=leave_type_annual,
        year=datetime.date.today().year,
        allocated_days=Decimal("16"),
        used_days=Decimal("0"),
    )
