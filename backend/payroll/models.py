"""Payroll models: tax settings, salary structures, payroll runs, payslips."""
from django.db import models


class PayrollStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    REVIEWED = "REVIEWED", "Reviewed"
    APPROVED = "APPROVED", "Approved"
    PAID = "PAID", "Paid"


class TaxBracket(models.Model):
    """Ethiopian income tax bracket — stored in DB, editable by Admin."""

    min_income = models.DecimalField(max_digits=12, decimal_places=2)
    max_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                     help_text="Null means no upper limit (top bracket)")
    rate = models.DecimalField(max_digits=5, decimal_places=4, help_text="e.g. 0.15 for 15%")
    deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                    help_text="Fixed deduction amount for this bracket")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["min_income"]

    def __str__(self):
        upper = f"{self.max_income}" if self.max_income else "∞"
        return f"{self.min_income}–{upper} @ {float(self.rate)*100:.0f}%"


class PensionSetting(models.Model):
    """Pension configuration — stored in DB."""

    employee_rate = models.DecimalField(max_digits=5, decimal_places=4, default="0.07")
    employer_rate = models.DecimalField(max_digits=5, decimal_places=4, default="0.11")
    pension_reduces_taxable_income = models.BooleanField(default=False)
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-effective_date"]

    def __str__(self):
        return f"Pension {self.employee_rate*100:.0f}%/{self.employer_rate*100:.0f}% (from {self.effective_date})"


class OvertimeRule(models.Model):
    """Overtime multiplier rules — stored in DB."""

    overtime_type = models.CharField(max_length=20, unique=True,
        choices=[("NORMAL", "Normal Day"), ("NIGHT", "Night"), ("REST", "Weekly Rest Day"), ("HOLIDAY", "Public Holiday")])
    multiplier = models.DecimalField(max_digits=4, decimal_places=2)
    hourly_divisor = models.DecimalField(max_digits=6, decimal_places=2, default=208,
                                         help_text="Monthly hours divisor for hourly rate (default 208)")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.overtime_type} × {self.multiplier}"


class SalaryStructure(models.Model):
    """Salary structure assigned to an employee."""

    employee = models.OneToOneField("employees.Employee", on_delete=models.CASCADE, related_name="salary")
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)

    # Taxable allowances
    housing_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_taxable_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Non-taxable allowances
    non_taxable_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} — Basic {self.basic_salary} ETB"

    @property
    def total_taxable_allowances(self):
        return self.housing_allowance + self.transport_allowance + self.other_taxable_allowance


class PayrollRun(models.Model):
    """One payroll run per month."""

    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=PayrollStatus.choices, default=PayrollStatus.DRAFT)

    prepared_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="prepared_payrolls"
    )
    reviewed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_payrolls"
    )
    approved_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_payrolls"
    )

    total_gross = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_net = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_employee_pension = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_employer_pension = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("year", "month")]
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"Payroll {self.year}/{self.month:02d} [{self.status}]"


class PayslipDeduction(models.TextChoices):
    LOAN = "LOAN", "Loan"
    ADVANCE = "ADVANCE", "Advance"
    PENALTY = "PENALTY", "Penalty"
    OTHER = "OTHER", "Other"


class Payslip(models.Model):
    """Individual employee payslip for a payroll run."""

    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name="payslips")
    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE, related_name="payslips")
    salary_structure = models.ForeignKey(SalaryStructure, on_delete=models.SET_NULL, null=True)

    # Earnings
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    taxable_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    non_taxable_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Computed
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    taxable_income = models.DecimalField(max_digits=12, decimal_places=2)
    income_tax = models.DecimalField(max_digits=10, decimal_places=2)
    employee_pension = models.DecimalField(max_digits=10, decimal_places=2)
    employer_pension = models.DecimalField(max_digits=10, decimal_places=2)

    # Other deductions
    loan_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    penalty_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    net_pay = models.DecimalField(max_digits=12, decimal_places=2)

    pdf_file = models.FileField(upload_to="payslips/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("payroll_run", "employee")]
        ordering = ["employee__last_name"]

    def __str__(self):
        return f"{self.employee} — {self.payroll_run}"
