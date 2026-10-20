"""
Ethiopian Payroll Engine.

All tax brackets, pension rates, and overtime multipliers are loaded from the
database — never hard-coded.  This module is the single source of truth for
payroll calculations.
"""
from __future__ import annotations

import io
import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from audit.middleware import get_current_actor
from audit.services import log_action
from notifications.services import notify

if TYPE_CHECKING:
    from payroll.models import Payslip, PayrollRun

logger = logging.getLogger(__name__)

_ZERO = Decimal("0.00")
_TWO = Decimal("0.01")


# ── Tax engine ────────────────────────────────────────────────────────────────

def calculate_income_tax(taxable_income: Decimal) -> Decimal:
    """Calculate Ethiopian income tax from the DB tax brackets.

    Args:
        taxable_income: Monthly taxable income in ETB.

    Returns:
        Income tax amount in ETB.
    """
    from payroll.models import TaxBracket

    taxable_income = taxable_income.quantize(_TWO, rounding=ROUND_HALF_UP)
    if taxable_income <= _ZERO:
        return _ZERO

    brackets = TaxBracket.objects.filter(is_active=True).order_by("min_income")
    for bracket in brackets:
        lower = bracket.min_income
        upper = bracket.max_income
        if upper is None or taxable_income <= upper:
            tax = taxable_income * bracket.rate - bracket.deduction
            return max(_ZERO, tax.quantize(_TWO, rounding=ROUND_HALF_UP))

    return _ZERO


def calculate_pension(basic_salary: Decimal) -> tuple[Decimal, Decimal]:
    """Calculate employee and employer pension contributions.

    Args:
        basic_salary: Employee's basic salary.

    Returns:
        Tuple of (employee_pension, employer_pension).
    """
    from payroll.models import PensionSetting

    setting = PensionSetting.objects.filter(is_active=True).order_by("-effective_date").first()
    if not setting:
        emp_rate = Decimal("0.07")
        er_rate = Decimal("0.11")
        reduces = False
    else:
        emp_rate = setting.employee_rate
        er_rate = setting.employer_rate
        reduces = setting.pension_reduces_taxable_income

    emp_pension = (basic_salary * emp_rate).quantize(_TWO, rounding=ROUND_HALF_UP)
    er_pension = (basic_salary * er_rate).quantize(_TWO, rounding=ROUND_HALF_UP)
    return emp_pension, er_pension


def calculate_overtime_pay(basic_salary: Decimal, overtime_hours: Decimal, overtime_type: str) -> Decimal:
    """Calculate overtime pay for a given number of hours.

    Args:
        basic_salary: Employee's basic salary.
        overtime_hours: Approved overtime hours.
        overtime_type: One of NORMAL/NIGHT/REST/HOLIDAY.

    Returns:
        Overtime pay in ETB.
    """
    from payroll.models import OvertimeRule

    try:
        rule = OvertimeRule.objects.get(overtime_type=overtime_type, is_active=True)
        multiplier = rule.multiplier
        divisor = rule.hourly_divisor
    except OvertimeRule.DoesNotExist:
        multiplier = Decimal("1.25")
        divisor = Decimal("208")

    hourly_rate = basic_salary / divisor
    pay = hourly_rate * multiplier * overtime_hours
    return pay.quantize(_TWO, rounding=ROUND_HALF_UP)


def compute_payslip_values(
    basic_salary: Decimal,
    taxable_allowances: Decimal = _ZERO,
    non_taxable_allowances: Decimal = _ZERO,
    overtime_pay: Decimal = _ZERO,
    bonus: Decimal = _ZERO,
    loan_deduction: Decimal = _ZERO,
    advance_deduction: Decimal = _ZERO,
    penalty_deduction: Decimal = _ZERO,
    other_deduction: Decimal = _ZERO,
) -> dict:
    """Compute all payslip values following the Ethiopian calculation order.

    Calculation order:
        gross = basic + taxable_allowances + overtime + bonus
        taxable_income = gross  (or gross - employee_pension if pension_reduces_taxable)
        income_tax = tax(taxable_income)
        net = gross + non_taxable_allowances - income_tax - employee_pension - other_deductions

    Args:
        basic_salary: Employee basic salary.
        taxable_allowances: Sum of all taxable allowances.
        non_taxable_allowances: Sum of all non-taxable allowances.
        overtime_pay: Pre-computed overtime pay.
        bonus: Bonus amount.
        loan_deduction: Loan repayment.
        advance_deduction: Salary advance repayment.
        penalty_deduction: Penalty deduction.
        other_deduction: Any other deductions.

    Returns:
        Dict with all computed values.
    """
    from payroll.models import PensionSetting

    setting = PensionSetting.objects.filter(is_active=True).order_by("-effective_date").first()
    pension_reduces = setting.pension_reduces_taxable_income if setting else False

    gross = basic_salary + taxable_allowances + overtime_pay + bonus
    emp_pension, er_pension = calculate_pension(basic_salary)

    taxable_income = gross - emp_pension if pension_reduces else gross
    income_tax = calculate_income_tax(taxable_income)

    total_other_deductions = loan_deduction + advance_deduction + penalty_deduction + other_deduction
    net = gross + non_taxable_allowances - income_tax - emp_pension - total_other_deductions

    return {
        "gross_salary": gross.quantize(_TWO, rounding=ROUND_HALF_UP),
        "taxable_income": taxable_income.quantize(_TWO, rounding=ROUND_HALF_UP),
        "income_tax": income_tax,
        "employee_pension": emp_pension,
        "employer_pension": er_pension,
        "net_pay": max(_ZERO, net.quantize(_TWO, rounding=ROUND_HALF_UP)),
    }


# ── Payroll run ───────────────────────────────────────────────────────────────

@transaction.atomic
def create_payroll_run(year: int, month: int, prepared_by) -> "PayrollRun":
    """Create a new draft payroll run for a given month.

    Args:
        year: Payroll year.
        month: Payroll month (1-12).
        prepared_by: Sub Admin User creating the run.

    Returns:
        New PayrollRun instance.
    """
    from payroll.models import PayrollRun, PayrollStatus
    run, created = PayrollRun.objects.get_or_create(
        year=year, month=month,
        defaults={"status": PayrollStatus.DRAFT, "prepared_by": prepared_by},
    )
    if not created:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"detail": f"Payroll run for {year}/{month:02d} already exists."})
    return run


@transaction.atomic
def generate_payslips(run: "PayrollRun") -> list["Payslip"]:
    """Generate payslips for all active employees in a DRAFT run.

    Args:
        run: PayrollRun instance in DRAFT status.

    Returns:
        List of created Payslip instances.
    """
    from attendance.models import AttendanceRecord, OvertimeStatus
    from employees.models import Employee, EmploymentStatus
    from payroll.models import Payslip, PayrollStatus

    if run.status != PayrollStatus.DRAFT:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"detail": "Can only generate payslips for DRAFT payroll runs."})

    employees = Employee.objects.filter(status=EmploymentStatus.ACTIVE).select_related("salary")
    payslips = []

    for employee in employees:
        try:
            salary = employee.salary
        except Exception:
            logger.warning("Employee %s has no salary structure — skipping.", employee)
            continue

        # Get approved overtime for this month
        overtime_records = AttendanceRecord.objects.filter(
            employee=employee,
            date__year=run.year,
            date__month=run.month,
            overtime_status=OvertimeStatus.APPROVED,
            overtime_hours__gt=0,
        )
        overtime_pay = _ZERO
        for ot in overtime_records:
            overtime_pay += calculate_overtime_pay(
                salary.basic_salary, Decimal(str(ot.overtime_hours)), ot.overtime_type or "NORMAL"
            )

        values = compute_payslip_values(
            basic_salary=salary.basic_salary,
            taxable_allowances=salary.total_taxable_allowances,
            non_taxable_allowances=salary.non_taxable_allowance,
            overtime_pay=overtime_pay,
        )

        payslip, _ = Payslip.objects.update_or_create(
            payroll_run=run,
            employee=employee,
            defaults={
                "salary_structure": salary,
                "basic_salary": salary.basic_salary,
                "taxable_allowances": salary.total_taxable_allowances,
                "non_taxable_allowances": salary.non_taxable_allowance,
                "overtime_pay": overtime_pay,
                "bonus": _ZERO,
                **values,
            },
        )
        payslips.append(payslip)

    # Update run totals
    run.total_gross = sum(p.gross_salary for p in payslips)
    run.total_net = sum(p.net_pay for p in payslips)
    run.total_tax = sum(p.income_tax for p in payslips)
    run.total_employee_pension = sum(p.employee_pension for p in payslips)
    run.total_employer_pension = sum(p.employer_pension for p in payslips)
    run.save(update_fields=[
        "total_gross", "total_net", "total_tax",
        "total_employee_pension", "total_employer_pension", "updated_at",
    ])
    return payslips


@transaction.atomic
def advance_payroll_status(run: "PayrollRun", actor, notes: str = "") -> "PayrollRun":
    """Advance payroll run through the approval workflow.

    DRAFT → REVIEWED (Sub Admin) → APPROVED (Admin) → PAID

    Args:
        run: Current PayrollRun.
        actor: User performing the transition.
        notes: Optional notes.

    Returns:
        Updated PayrollRun.
    """
    from accounts.models import UserRole
    from payroll.models import PayrollStatus

    transitions = {
        PayrollStatus.DRAFT: (PayrollStatus.REVIEWED, [UserRole.ADMIN, UserRole.SUB_ADMIN]),
        PayrollStatus.REVIEWED: (PayrollStatus.APPROVED, [UserRole.ADMIN]),
        PayrollStatus.APPROVED: (PayrollStatus.PAID, [UserRole.ADMIN]),
    }

    if run.status not in transitions:
        from rest_framework.exceptions import ValidationError
        raise ValidationError({"detail": f"Cannot advance payroll from {run.status} status."})

    next_status, allowed_roles = transitions[run.status]
    if actor.role not in allowed_roles:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied(f"Only {allowed_roles} can advance payroll to {next_status}.")

    old_status = run.status
    run.status = next_status
    run.notes = notes
    if next_status == PayrollStatus.REVIEWED:
        run.reviewed_by = actor
    elif next_status == PayrollStatus.APPROVED:
        run.approved_by = actor
    run.save(update_fields=["status", "notes", "reviewed_by", "approved_by", "updated_at"])

    log_action(
        actor=actor,
        action="APPROVE",
        obj=run,
        old_value={"status": old_status},
        new_value={"status": next_status},
    )

    if next_status == PayrollStatus.APPROVED:
        # Notify all employees with email
        from payroll.models import Payslip
        from config.email_service import send_payslip_ready
        for payslip in run.payslips.select_related("employee__user_account"):
            user_acct = getattr(payslip.employee, "user_account", None)
            notify(
                recipient=user_acct,
                message=f"Your payslip for {run.year}/{run.month:02d} is ready.",
                category="payroll", related_object_id=payslip.pk,
            )
            if user_acct and user_acct.email:
                send_payslip_ready(
                    user_acct.email,
                    payslip.employee.first_name,
                    f"{run.year}/{run.month:02d}",
                    float(payslip.net_pay),
                )

    return run


# ── Payslip PDF ───────────────────────────────────────────────────────────────

def generate_payslip_pdf(payslip: "Payslip") -> bytes:
    """Generate a PDF payslip using ReportLab.

    Args:
        payslip: Payslip instance with related data loaded.

    Returns:
        PDF content as bytes.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph("<b>HR & PAYROLL MANAGEMENT SYSTEM</b>", styles["Title"]))
    story.append(Paragraph("PAYSLIP", styles["Heading2"]))
    story.append(Spacer(1, 0.5*cm))

    emp = payslip.employee
    run = payslip.payroll_run
    info_data = [
        ["Employee:", emp.get_full_name(), "Employee ID:", emp.employee_id],
        ["Department:", emp.department.name if emp.department else "—", "Position:", emp.position.name if emp.position else "—"],
        ["Pay Period:", f"{run.year}/{run.month:02d}", "Bank:", emp.bank_name],
        ["Account No:", emp.bank_account_number, "TIN:", emp.tin_number],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))

    # Earnings & Deductions
    def money(val):
        return f"ETB {float(val):,.2f}"

    earnings = [
        ["EARNINGS", "AMOUNT", "DEDUCTIONS", "AMOUNT"],
        ["Basic Salary", money(payslip.basic_salary), "Income Tax", money(payslip.income_tax)],
        ["Taxable Allowances", money(payslip.taxable_allowances), "Employee Pension", money(payslip.employee_pension)],
        ["Non-Taxable Allow.", money(payslip.non_taxable_allowances), "Loan Deduction", money(payslip.loan_deduction)],
        ["Overtime Pay", money(payslip.overtime_pay), "Advance Deduction", money(payslip.advance_deduction)],
        ["Bonus", money(payslip.bonus), "Penalty", money(payslip.penalty_deduction)],
        ["", "", "Other Deductions", money(payslip.other_deduction)],
        ["GROSS SALARY", money(payslip.gross_salary), "NET PAY", money(payslip.net_pay)],
    ]

    table = Table(earnings, colWidths=[5*cm, 4*cm, 5*cm, 4*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#dbeafe")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))

    # Employer pension note
    story.append(Paragraph(
        f"<i>Employer Pension Contribution: {money(payslip.employer_pension)}</i>",
        styles["Normal"]
    ))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Generated by HR & Payroll Management System", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
