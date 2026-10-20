"""
Seed demo data for the HR Payroll system.

Run: python manage.py seed_demo

Creates:
- 4 users (one per role)
- 2 departments, 3 positions, 1 branch
- 3 public holidays
- Tax brackets, pension settings, overtime rules
- 3 employee profiles with salary structures
- 1 month of attendance records
- 1 payroll run (Draft)
- 2 leave types + leave balances
- 2 leave requests
"""
from __future__ import annotations

import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed demo data for HR Payroll system"

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding demo data..."))

        # ── Organization ──────────────────────────────────────────────────────
        from organization.models import Branch, Department, Position, PublicHoliday

        engineering, _ = Department.objects.get_or_create(
            code="ENG", defaults={"name": "Engineering", "description": "Software Engineering dept"}
        )
        hr_dept, _ = Department.objects.get_or_create(
            code="HR", defaults={"name": "Human Resources", "description": "HR department"}
        )

        p_se, _ = Position.objects.get_or_create(
            name="Software Engineer", department=engineering, defaults={"grade": "Grade 3"}
        )
        p_sr, _ = Position.objects.get_or_create(
            name="Senior Engineer", department=engineering, defaults={"grade": "Grade 5"}
        )
        p_hr, _ = Position.objects.get_or_create(
            name="HR Officer", department=hr_dept, defaults={"grade": "Grade 2"}
        )

        branch_hq, _ = Branch.objects.get_or_create(
            name="Headquarters", defaults={"city": "Addis Ababa", "address": "Bole Road, AA"}
        )

        today = timezone.now().date()
        year = today.year
        PublicHoliday.objects.get_or_create(
            name="Ethiopian New Year", date=datetime.date(year, 9, 11),
            defaults={"holiday_type": "NATIONAL"}
        )
        PublicHoliday.objects.get_or_create(
            name="Meskel", date=datetime.date(year, 9, 27),
            defaults={"holiday_type": "RELIGIOUS"}
        )
        PublicHoliday.objects.get_or_create(
            name="Christmas (Genna)", date=datetime.date(year, 1, 7),
            defaults={"holiday_type": "RELIGIOUS"}
        )
        self.stdout.write("  ✓ Organization data")

        # ── Payroll settings ──────────────────────────────────────────────────
        from payroll.models import OvertimeRule, PensionSetting, TaxBracket

        brackets = [
            (Decimal("0"), Decimal("2000"), Decimal("0"), Decimal("0")),
            (Decimal("2001"), Decimal("4000"), Decimal("0.15"), Decimal("300")),
            (Decimal("4001"), Decimal("7000"), Decimal("0.20"), Decimal("500")),
            (Decimal("7001"), Decimal("10000"), Decimal("0.25"), Decimal("850")),
            (Decimal("10001"), Decimal("14000"), Decimal("0.30"), Decimal("1350")),
            (Decimal("14001"), None, Decimal("0.35"), Decimal("2050")),
        ]
        TaxBracket.objects.all().delete()
        for min_i, max_i, rate, ded in brackets:
            TaxBracket.objects.create(
                min_income=min_i, max_income=max_i, rate=rate, deduction=ded
            )

        PensionSetting.objects.get_or_create(
            effective_date=datetime.date(2020, 1, 1),
            defaults={
                "employee_rate": Decimal("0.07"),
                "employer_rate": Decimal("0.11"),
                "pension_reduces_taxable_income": False,
            }
        )

        ot_rules = [
            ("NORMAL", Decimal("1.25")),
            ("NIGHT", Decimal("1.50")),
            ("REST", Decimal("2.00")),
            ("HOLIDAY", Decimal("2.50")),
        ]
        for ot_type, mult in ot_rules:
            OvertimeRule.objects.get_or_create(overtime_type=ot_type, defaults={"multiplier": mult})
        self.stdout.write("  ✓ Tax brackets and payroll settings")

        # ── Leave types ───────────────────────────────────────────────────────
        from leave.models import LeaveType

        leave_types = [
            ("ANNUAL", "Annual Leave", 16, True),
            ("SICK", "Sick Leave", 10, True),
            ("MATERNITY", "Maternity Leave", 90, True),
            ("PATERNITY", "Paternity Leave", 3, True),
            ("UNPAID", "Unpaid Leave", 0, False),
        ]
        for code, name, days, paid in leave_types:
            LeaveType.objects.get_or_create(
                code=code, defaults={"name": name, "default_days_per_year": days, "is_paid": paid}
            )
        self.stdout.write("  ✓ Leave types")

        # ── Users ─────────────────────────────────────────────────────────────
        from accounts.models import SubAdminPermission, User, UserRole, PermissionModule

        admin_user, _ = User.objects.get_or_create(
            email="admin@hrpayroll.et",
            defaults={
                "first_name": "Admin", "last_name": "User",
                "role": UserRole.ADMIN, "is_staff": True, "is_superuser": True,
            }
        )
        admin_user.set_password("Admin@1234")
        admin_user.save()

        subadmin_user, _ = User.objects.get_or_create(
            email="subadmin@hrpayroll.et",
            defaults={
                "first_name": "HR", "last_name": "Officer",
                "role": UserRole.SUB_ADMIN,
            }
        )
        subadmin_user.set_password("SubAdmin@1234")
        subadmin_user.save()

        # Grant all permissions to sub admin
        for module in PermissionModule.values:
            SubAdminPermission.objects.get_or_create(
                user=subadmin_user, module=module,
                defaults={"can_view": True, "can_create": True, "can_edit": True, "can_delete": True, "can_approve": True}
            )

        manager_user, _ = User.objects.get_or_create(
            email="manager@hrpayroll.et",
            defaults={
                "first_name": "Department", "last_name": "Manager",
                "role": UserRole.MANAGER, "managed_department": engineering,
            }
        )
        manager_user.set_password("Manager@1234")
        manager_user.save()

        employee_user, _ = User.objects.get_or_create(
            email="employee@hrpayroll.et",
            defaults={
                "first_name": "John", "last_name": "Employee",
                "role": UserRole.EMPLOYEE,
            }
        )
        employee_user.set_password("Employee@1234")
        employee_user.save()
        self.stdout.write("  ✓ Users (admin, subadmin, manager, employee)")

        # ── Employees ─────────────────────────────────────────────────────────
        from employees.models import Employee, EmploymentContract

        emp1, _ = Employee.objects.get_or_create(
            employee_id="EMP-00001",
            defaults={
                "first_name": "Abebe", "last_name": "Bekele",
                "department": engineering, "position": p_se, "branch": branch_hq,
                "hire_date": datetime.date(2022, 1, 15),
                "tin_number": "TIN001001", "pension_number": "PEN001001",
                "bank_name": "Commercial Bank of Ethiopia", "bank_account_number": "1000123456789",
                "phone_number": "+251911123456",
            }
        )
        emp2, _ = Employee.objects.get_or_create(
            employee_id="EMP-00002",
            defaults={
                "first_name": "Tigist", "last_name": "Haile",
                "department": engineering, "position": p_sr, "branch": branch_hq,
                "hire_date": datetime.date(2020, 3, 1),
                "tin_number": "TIN001002", "pension_number": "PEN001002",
                "bank_name": "Awash Bank", "bank_account_number": "2000987654321",
                "phone_number": "+251922234567",
            }
        )
        emp3, _ = Employee.objects.get_or_create(
            employee_id="EMP-00003",
            defaults={
                "first_name": "Meron", "last_name": "Tadesse",
                "department": hr_dept, "position": p_hr, "branch": branch_hq,
                "hire_date": datetime.date(2023, 6, 1),
                "tin_number": "TIN001003", "pension_number": "PEN001003",
                "bank_name": "Dashen Bank", "bank_account_number": "3000111222333",
                "phone_number": "+251933345678",
            }
        )

        # Link employee user to emp1
        if not employee_user.employee:
            employee_user.employee = emp1
            employee_user.save(update_fields=["employee"])

        # Contracts
        for emp in [emp1, emp2, emp3]:
            EmploymentContract.objects.get_or_create(
                employee=emp, contract_type="PERMANENT",
                defaults={"start_date": emp.hire_date, "is_active": True}
            )
        self.stdout.write("  ✓ Employee profiles")

        # ── Salary structures ─────────────────────────────────────────────────
        from payroll.models import SalaryStructure

        SalaryStructure.objects.get_or_create(
            employee=emp1,
            defaults={
                "basic_salary": Decimal("10000"),
                "housing_allowance": Decimal("2000"),
                "transport_allowance": Decimal("500"),
                "non_taxable_allowance": Decimal("300"),
                "effective_date": emp1.hire_date,
            }
        )
        SalaryStructure.objects.get_or_create(
            employee=emp2,
            defaults={
                "basic_salary": Decimal("15000"),
                "housing_allowance": Decimal("3000"),
                "transport_allowance": Decimal("800"),
                "non_taxable_allowance": Decimal("500"),
                "effective_date": emp2.hire_date,
            }
        )
        SalaryStructure.objects.get_or_create(
            employee=emp3,
            defaults={
                "basic_salary": Decimal("8000"),
                "housing_allowance": Decimal("1500"),
                "transport_allowance": Decimal("400"),
                "non_taxable_allowance": Decimal("200"),
                "effective_date": emp3.hire_date,
            }
        )
        self.stdout.write("  ✓ Salary structures")

        # ── Attendance records (current month) ────────────────────────────────
        from attendance.models import AttendanceRecord, AttendanceStatus

        import calendar
        start_day = today.replace(day=1)
        weekdays_this_month = [
            start_day + datetime.timedelta(days=i)
            for i in range((today - start_day).days + 1)
            if (start_day + datetime.timedelta(days=i)).weekday() < 5
        ]
        for emp in [emp1, emp2, emp3]:
            for work_day in weekdays_this_month[:15]:  # Seed first 15 weekdays
                AttendanceRecord.objects.get_or_create(
                    employee=emp, date=work_day,
                    defaults={
                        "check_in": datetime.time(8, 30),
                        "check_out": datetime.time(17, 30),
                        "status": AttendanceStatus.PRESENT,
                    }
                )
        self.stdout.write("  ✓ Attendance records")

        # ── Leave balances ────────────────────────────────────────────────────
        from leave.models import LeaveBalance, LeaveRequest, LeaveStatus

        annual_type = LeaveType.objects.get(code="ANNUAL")
        sick_type = LeaveType.objects.get(code="SICK")

        for emp in [emp1, emp2, emp3]:
            LeaveBalance.objects.get_or_create(
                employee=emp, leave_type=annual_type, year=year,
                defaults={"allocated_days": Decimal("16")}
            )
            LeaveBalance.objects.get_or_create(
                employee=emp, leave_type=sick_type, year=year,
                defaults={"allocated_days": Decimal("10")}
            )

        # ── Leave requests ────────────────────────────────────────────────────
        next_week = today + datetime.timedelta(days=7)
        LeaveRequest.objects.get_or_create(
            employee=emp1,
            start_date=next_week,
            end_date=next_week + datetime.timedelta(days=2),
            defaults={
                "leave_type": annual_type,
                "number_of_days": Decimal("3"),
                "reason": "Family event",
                "status": LeaveStatus.PENDING,
            }
        )
        LeaveRequest.objects.get_or_create(
            employee=emp2,
            start_date=today,
            end_date=today + datetime.timedelta(days=1),
            defaults={
                "leave_type": sick_type,
                "number_of_days": Decimal("2"),
                "reason": "Medical appointment",
                "status": LeaveStatus.MANAGER_APPROVED,
                "manager_approved_by": manager_user,
                "manager_approved_at": timezone.now(),
            }
        )
        self.stdout.write("  ✓ Leave requests")

        # ── Payroll run (Draft) ───────────────────────────────────────────────
        from payroll.models import PayrollRun, PayrollStatus

        PayrollRun.objects.get_or_create(
            year=year, month=today.month,
            defaults={"status": PayrollStatus.DRAFT, "prepared_by": subadmin_user}
        )
        self.stdout.write("  ✓ Payroll run (Draft)")

        self.stdout.write(self.style.SUCCESS("\n✅ Demo data seeded successfully!\n"))
        self.stdout.write("  Login credentials:")
        self.stdout.write("  admin@hrpayroll.et    / Admin@1234    (Admin)")
        self.stdout.write("  subadmin@hrpayroll.et / SubAdmin@1234 (Sub Admin)")
        self.stdout.write("  manager@hrpayroll.et  / Manager@1234  (Manager)")
        self.stdout.write("  employee@hrpayroll.et / Employee@1234 (Employee)")
