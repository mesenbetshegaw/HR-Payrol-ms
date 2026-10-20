from django.contrib import admin
from payroll.models import OvertimeRule, PayrollRun, Payslip, PensionSetting, SalaryStructure, TaxBracket


@admin.register(TaxBracket)
class TaxBracketAdmin(admin.ModelAdmin):
    list_display = ["min_income", "max_income", "rate", "deduction", "is_active"]


@admin.register(PensionSetting)
class PensionSettingAdmin(admin.ModelAdmin):
    list_display = ["employee_rate", "employer_rate", "pension_reduces_taxable_income", "effective_date", "is_active"]


@admin.register(OvertimeRule)
class OvertimeRuleAdmin(admin.ModelAdmin):
    list_display = ["overtime_type", "multiplier", "hourly_divisor", "is_active"]


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = ["employee", "basic_salary", "effective_date", "is_active"]
    search_fields = ["employee__first_name", "employee__last_name"]


@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    list_display = ["year", "month", "status", "total_gross", "total_net", "prepared_by"]
    list_filter = ["status"]


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ["employee", "payroll_run", "gross_salary", "income_tax", "net_pay"]
    search_fields = ["employee__first_name", "employee__last_name"]
    list_filter = ["payroll_run"]
