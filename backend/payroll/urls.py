from django.urls import path
from payroll import views

urlpatterns = [
    # Settings (Admin)
    path("tax-brackets/", views.TaxBracketListCreateView.as_view(), name="tax-bracket-list"),
    path("tax-brackets/<int:pk>/", views.TaxBracketDetailView.as_view(), name="tax-bracket-detail"),
    path("pension-settings/", views.PensionSettingListCreateView.as_view(), name="pension-list"),
    path("pension-settings/<int:pk>/", views.PensionSettingDetailView.as_view(), name="pension-detail"),
    path("overtime-rules/", views.OvertimeRuleListCreateView.as_view(), name="overtime-rule-list"),
    path("overtime-rules/<int:pk>/", views.OvertimeRuleDetailView.as_view(), name="overtime-rule-detail"),
    # Salary
    path("salary/", views.SalaryStructureListCreateView.as_view(), name="salary-list"),
    path("salary/<int:pk>/", views.SalaryStructureDetailView.as_view(), name="salary-detail"),
    # Payroll runs
    path("runs/", views.PayrollRunListCreateView.as_view(), name="payroll-run-list"),
    path("runs/<int:pk>/", views.PayrollRunDetailView.as_view(), name="payroll-run-detail"),
    path("runs/<int:pk>/generate/", views.GeneratePayslipsView.as_view(), name="payroll-generate"),
    path("runs/<int:pk>/advance/", views.AdvancePayrollStatusView.as_view(), name="payroll-advance"),
    path("runs/<int:pk>/bank-transfer/", views.BankTransferExportView.as_view(), name="bank-transfer"),
    # Payslips
    path("payslips/", views.PayslipListView.as_view(), name="payslip-list"),
    path("payslips/<int:pk>/", views.PayslipDetailView.as_view(), name="payslip-detail"),
    path("payslips/<int:pk>/pdf/", views.PayslipPDFView.as_view(), name="payslip-pdf"),
]
