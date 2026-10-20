"""
Tests for the Ethiopian payroll engine.

Unit test example from spec:
  basic=10,000, no allowances
  → employee_pension=700, employer_pension=1,100, income_tax=1,650, net=7,650
"""
import datetime
from decimal import Decimal

import pytest

from payroll.services import (
    calculate_income_tax,
    calculate_pension,
    compute_payslip_values,
)


@pytest.mark.django_db
class TestIncomeTax:
    """Test every tax bracket boundary."""

    def test_zero_income(self, tax_brackets, pension_setting):
        assert calculate_income_tax(Decimal("0")) == Decimal("0.00")

    def test_below_first_bracket(self, tax_brackets, pension_setting):
        # 0–2000 → 0%
        assert calculate_income_tax(Decimal("2000")) == Decimal("0.00")
        assert calculate_income_tax(Decimal("1500")) == Decimal("0.00")

    def test_second_bracket(self, tax_brackets, pension_setting):
        # 2001–4000 → 15% − 300
        # 3000 * 0.15 − 300 = 150
        result = calculate_income_tax(Decimal("3000"))
        assert result == Decimal("150.00")

    def test_third_bracket(self, tax_brackets, pension_setting):
        # 4001–7000 → 20% − 500
        # 5000 * 0.20 − 500 = 500
        result = calculate_income_tax(Decimal("5000"))
        assert result == Decimal("500.00")

    def test_fourth_bracket(self, tax_brackets, pension_setting):
        # 7001–10000 → 25% − 850
        # 10000 * 0.25 − 850 = 1650
        result = calculate_income_tax(Decimal("10000"))
        assert result == Decimal("1650.00")

    def test_fifth_bracket(self, tax_brackets, pension_setting):
        # 10001–14000 → 30% − 1350
        # 12000 * 0.30 − 1350 = 2250
        result = calculate_income_tax(Decimal("12000"))
        assert result == Decimal("2250.00")

    def test_top_bracket(self, tax_brackets, pension_setting):
        # above 14000 → 35% − 2050
        # 20000 * 0.35 − 2050 = 4950
        result = calculate_income_tax(Decimal("20000"))
        assert result == Decimal("4950.00")

    def test_bracket_boundary_2001(self, tax_brackets, pension_setting):
        # Just above first bracket
        result = calculate_income_tax(Decimal("2001"))
        expected = Decimal("2001") * Decimal("0.15") - Decimal("300")
        assert result == expected.quantize(Decimal("0.01"))


@pytest.mark.django_db
class TestPension:
    def test_pension_rates(self, pension_setting):
        emp, er = calculate_pension(Decimal("10000"))
        assert emp == Decimal("700.00")   # 7%
        assert er == Decimal("1100.00")   # 11%

    def test_pension_zero_salary(self, pension_setting):
        emp, er = calculate_pension(Decimal("0"))
        assert emp == Decimal("0.00")
        assert er == Decimal("0.00")


@pytest.mark.django_db
class TestComputePayslip:
    """Full payslip calculation tests."""

    def test_spec_example(self, tax_brackets, pension_setting):
        """
        From the specification:
        basic=10,000, no allowances
        → employee_pension=700, employer_pension=1,100, income_tax=1,650, net=7,650
        """
        result = compute_payslip_values(basic_salary=Decimal("10000"))

        assert result["employee_pension"] == Decimal("700.00")
        assert result["employer_pension"] == Decimal("1100.00")
        assert result["income_tax"] == Decimal("1650.00")
        assert result["net_pay"] == Decimal("7650.00")
        assert result["gross_salary"] == Decimal("10000.00")

    def test_with_taxable_allowance(self, tax_brackets, pension_setting):
        """Taxable allowances raise gross and therefore income tax."""
        result = compute_payslip_values(
            basic_salary=Decimal("10000"),
            taxable_allowances=Decimal("2000"),
        )
        # gross = 12000
        # tax = 12000 * 0.30 - 1350 = 2250
        assert result["gross_salary"] == Decimal("12000.00")
        assert result["income_tax"] == Decimal("2250.00")

    def test_with_non_taxable_allowance(self, tax_brackets, pension_setting):
        """Non-taxable allowances increase net pay but not tax."""
        without = compute_payslip_values(basic_salary=Decimal("10000"))
        with_nta = compute_payslip_values(
            basic_salary=Decimal("10000"),
            non_taxable_allowances=Decimal("1000"),
        )
        assert with_nta["income_tax"] == without["income_tax"]
        assert with_nta["net_pay"] == without["net_pay"] + Decimal("1000")

    def test_with_deductions(self, tax_brackets, pension_setting):
        """Other deductions reduce net pay."""
        result = compute_payslip_values(
            basic_salary=Decimal("10000"),
            loan_deduction=Decimal("500"),
            advance_deduction=Decimal("200"),
        )
        # net = 7650 - 500 - 200 = 6950
        assert result["net_pay"] == Decimal("6950.00")

    def test_net_never_negative(self, tax_brackets, pension_setting):
        """Net pay should never go below zero."""
        result = compute_payslip_values(
            basic_salary=Decimal("2000"),
            other_deduction=Decimal("99999"),
        )
        assert result["net_pay"] == Decimal("0.00")

    def test_bracket_5000(self, tax_brackets, pension_setting):
        # bracket: 4001-7000 → 20% - 500
        # gross=5000, tax=5000*0.20-500=500, pension=350, net=5000-500-350=4150
        result = compute_payslip_values(basic_salary=Decimal("5000"))
        assert result["income_tax"] == Decimal("500.00")
        assert result["employee_pension"] == Decimal("350.00")
        assert result["net_pay"] == Decimal("4150.00")

    def test_bracket_3000(self, tax_brackets, pension_setting):
        # bracket: 2001-4000 → 15% - 300
        # gross=3000, tax=3000*0.15-300=150, pension=210, net=3000-150-210=2640
        result = compute_payslip_values(basic_salary=Decimal("3000"))
        assert result["income_tax"] == Decimal("150.00")
        assert result["employee_pension"] == Decimal("210.00")
        assert result["net_pay"] == Decimal("2640.00")


@pytest.mark.django_db
class TestPayrollRun:
    def test_create_payroll_run(self, admin_user, employee_profile, salary_structure, tax_brackets, pension_setting):
        from payroll.services import create_payroll_run, generate_payslips
        run = create_payroll_run(2025, 1, admin_user)
        assert run.status == "DRAFT"
        payslips = generate_payslips(run)
        assert len(payslips) == 1
        p = payslips[0]
        assert p.net_pay > 0
        assert p.income_tax > 0

    def test_advance_draft_to_reviewed(self, subadmin_user, employee_profile, salary_structure, tax_brackets, pension_setting):
        from payroll.services import create_payroll_run, generate_payslips, advance_payroll_status
        run = create_payroll_run(2025, 2, subadmin_user)
        generate_payslips(run)
        run.refresh_from_db()
        advanced = advance_payroll_status(run, subadmin_user)
        assert advanced.status == "REVIEWED"

    def test_only_admin_can_approve(self, subadmin_user, employee_profile, salary_structure, tax_brackets, pension_setting):
        from payroll.services import create_payroll_run, generate_payslips, advance_payroll_status
        from rest_framework.exceptions import PermissionDenied
        run = create_payroll_run(2025, 3, subadmin_user)
        generate_payslips(run)
        advance_payroll_status(run, subadmin_user)  # → REVIEWED
        run.refresh_from_db()
        with pytest.raises(PermissionDenied):
            advance_payroll_status(run, subadmin_user)  # Sub Admin cannot approve
