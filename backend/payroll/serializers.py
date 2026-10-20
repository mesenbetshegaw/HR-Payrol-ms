from rest_framework import serializers
from payroll.models import OvertimeRule, PayrollRun, Payslip, PensionSetting, SalaryStructure, TaxBracket


class TaxBracketSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxBracket
        fields = ["id", "min_income", "max_income", "rate", "deduction", "is_active"]


class PensionSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PensionSetting
        fields = ["id", "employee_rate", "employer_rate", "pension_reduces_taxable_income", "effective_date", "is_active"]


class OvertimeRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = OvertimeRule
        fields = ["id", "overtime_type", "multiplier", "hourly_divisor", "is_active"]


class SalaryStructureSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    total_taxable_allowances = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = SalaryStructure
        fields = [
            "id", "employee", "employee_name", "basic_salary",
            "housing_allowance", "transport_allowance", "other_taxable_allowance",
            "total_taxable_allowances", "non_taxable_allowance",
            "effective_date", "is_active", "created_at",
        ]
        read_only_fields = ["created_at", "total_taxable_allowances"]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()


class PayslipSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = Payslip
        fields = [
            "id", "payroll_run", "employee", "employee_name",
            "basic_salary", "taxable_allowances", "non_taxable_allowances",
            "overtime_pay", "bonus", "gross_salary", "taxable_income",
            "income_tax", "employee_pension", "employer_pension",
            "loan_deduction", "advance_deduction", "penalty_deduction", "other_deduction",
            "net_pay", "pdf_file", "created_at",
        ]
        read_only_fields = [
            "gross_salary", "taxable_income", "income_tax",
            "employee_pension", "employer_pension", "net_pay", "pdf_file", "created_at",
        ]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()


class PayrollRunSerializer(serializers.ModelSerializer):
    prepared_by_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    payslip_count = serializers.SerializerMethodField()

    class Meta:
        model = PayrollRun
        fields = [
            "id", "year", "month", "status",
            "prepared_by", "prepared_by_name",
            "reviewed_by", "reviewed_by_name",
            "approved_by", "approved_by_name",
            "total_gross", "total_net", "total_tax",
            "total_employee_pension", "total_employer_pension",
            "payslip_count", "notes", "created_at", "updated_at",
        ]
        read_only_fields = [
            "status", "total_gross", "total_net", "total_tax",
            "total_employee_pension", "total_employer_pension", "created_at", "updated_at",
        ]

    def get_prepared_by_name(self, obj):
        return obj.prepared_by.get_full_name() if obj.prepared_by else None

    def get_reviewed_by_name(self, obj):
        return obj.reviewed_by.get_full_name() if obj.reviewed_by else None

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None

    def get_payslip_count(self, obj):
        return obj.payslips.count()


class PayrollAdvanceSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default="")
