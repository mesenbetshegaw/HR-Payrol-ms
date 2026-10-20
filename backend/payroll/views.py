"""Payroll views."""
from __future__ import annotations

import io

import openpyxl
from django.http import FileResponse, HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserRole
from accounts.permissions import IsAdmin, IsAdminOrSubAdmin
from payroll import services
from payroll.models import OvertimeRule, PayrollRun, Payslip, PensionSetting, SalaryStructure, TaxBracket
from payroll.serializers import (
    OvertimeRuleSerializer, PayrollAdvanceSerializer, PayrollRunSerializer,
    PayslipSerializer, PensionSettingSerializer, SalaryStructureSerializer, TaxBracketSerializer,
)


# ── Settings (Admin only) ─────────────────────────────────────────────────────

@extend_schema(tags=["payroll-settings"])
class TaxBracketListCreateView(generics.ListCreateAPIView):
    serializer_class = TaxBracketSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = TaxBracket.objects.all()


@extend_schema(tags=["payroll-settings"])
class TaxBracketDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaxBracketSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = TaxBracket.objects.all()


@extend_schema(tags=["payroll-settings"])
class PensionSettingListCreateView(generics.ListCreateAPIView):
    serializer_class = PensionSettingSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = PensionSetting.objects.all()


@extend_schema(tags=["payroll-settings"])
class PensionSettingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PensionSettingSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = PensionSetting.objects.all()


@extend_schema(tags=["payroll-settings"])
class OvertimeRuleListCreateView(generics.ListCreateAPIView):
    serializer_class = OvertimeRuleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = OvertimeRule.objects.all()


@extend_schema(tags=["payroll-settings"])
class OvertimeRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OvertimeRuleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = OvertimeRule.objects.all()


# ── Salary structures ─────────────────────────────────────────────────────────

@extend_schema(tags=["payroll"])
class SalaryStructureListCreateView(generics.ListCreateAPIView):
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    search_fields = ["employee__first_name", "employee__last_name", "employee__employee_id"]
    filterset_fields = ["is_active"]

    def get_queryset(self):
        return SalaryStructure.objects.select_related("employee__department", "employee__position").all()

    def perform_create(self, serializer):
        from audit.services import log_action
        from audit.middleware import get_current_actor, get_client_ip, get_current_request
        salary = serializer.save()
        log_action(actor=get_current_actor(), action="CREATE", obj=salary,
                   new_value={"employee": salary.employee.employee_id, "basic": str(salary.basic_salary)},
                   ip_address=get_client_ip(get_current_request()) if get_current_request() else None)


@extend_schema(tags=["payroll"])
class SalaryStructureDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = SalaryStructureSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    queryset = SalaryStructure.objects.select_related("employee").all()

    def perform_update(self, serializer):
        from audit.services import log_action
        from audit.middleware import get_current_actor
        old = {"basic": str(self.get_object().basic_salary)}
        salary = serializer.save()
        log_action(actor=get_current_actor(), action="UPDATE", obj=salary,
                   old_value=old, new_value={"basic": str(salary.basic_salary)})


# ── Payroll runs ──────────────────────────────────────────────────────────────

@extend_schema(tags=["payroll"])
class PayrollRunListCreateView(generics.ListCreateAPIView):
    serializer_class = PayrollRunSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    filterset_fields = ["status", "year", "month"]
    ordering = ["-year", "-month"]

    def get_queryset(self):
        return PayrollRun.objects.select_related("prepared_by", "reviewed_by", "approved_by")

    def create(self, request, *args, **kwargs):
        year = request.data.get("year")
        month = request.data.get("month")
        if not year or not month:
            return Response({"detail": "year and month are required."}, status=400)
        run = services.create_payroll_run(int(year), int(month), request.user)
        return Response(PayrollRunSerializer(run).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["payroll"])
class PayrollRunDetailView(generics.RetrieveAPIView):
    serializer_class = PayrollRunSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    queryset = PayrollRun.objects.select_related("prepared_by", "reviewed_by", "approved_by")


@extend_schema(tags=["payroll"])
class GeneratePayslipsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def post(self, request: Request, pk: int) -> Response:
        try:
            run = PayrollRun.objects.get(pk=pk)
        except PayrollRun.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        payslips = services.generate_payslips(run)
        return Response({"detail": f"{len(payslips)} payslips generated.", "payroll_run": PayrollRunSerializer(run).data})


@extend_schema(tags=["payroll"])
class AdvancePayrollStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def post(self, request: Request, pk: int) -> Response:
        try:
            run = PayrollRun.objects.get(pk=pk)
        except PayrollRun.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        s = PayrollAdvanceSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        run = services.advance_payroll_status(run, request.user, s.validated_data.get("notes", ""))
        return Response(PayrollRunSerializer(run).data)


# ── Payslips ──────────────────────────────────────────────────────────────────

@extend_schema(tags=["payroll"])
class PayslipListView(generics.ListAPIView):
    serializer_class = PayslipSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["payroll_run", "employee"]

    def get_queryset(self):
        qs = Payslip.objects.select_related("employee", "payroll_run")
        user = self.request.user
        if user.role == UserRole.EMPLOYEE and hasattr(user, "employee"):
            qs = qs.filter(employee=user.employee)
        return qs


@extend_schema(tags=["payroll"])
class PayslipDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = PayslipSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    queryset = Payslip.objects.select_related("employee", "payroll_run")

    def perform_update(self, serializer):
        """Allow updating bonus and deductions, then recompute net pay."""
        payslip = self.get_object()
        data = serializer.validated_data
        # Recompute if any earning/deduction changed
        from payroll.services import compute_payslip_values
        from decimal import Decimal
        values = compute_payslip_values(
            basic_salary=data.get("basic_salary", payslip.basic_salary),
            taxable_allowances=data.get("taxable_allowances", payslip.taxable_allowances),
            non_taxable_allowances=data.get("non_taxable_allowances", payslip.non_taxable_allowances),
            overtime_pay=data.get("overtime_pay", payslip.overtime_pay),
            bonus=data.get("bonus", payslip.bonus),
            loan_deduction=data.get("loan_deduction", payslip.loan_deduction),
            advance_deduction=data.get("advance_deduction", payslip.advance_deduction),
            penalty_deduction=data.get("penalty_deduction", payslip.penalty_deduction),
            other_deduction=data.get("other_deduction", payslip.other_deduction),
        )
        serializer.save(**values)


@extend_schema(tags=["payroll"])
class PayslipPDFView(APIView):
    """Download payslip as PDF."""
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: int) -> FileResponse:
        try:
            payslip = Payslip.objects.select_related(
                "employee__department", "employee__position", "payroll_run"
            ).get(pk=pk)
        except Payslip.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        user = request.user
        if user.role == UserRole.EMPLOYEE:
            if not hasattr(user, "employee") or payslip.employee != user.employee:
                return Response({"detail": "Forbidden."}, status=403)

        pdf_bytes = services.generate_payslip_pdf(payslip)
        filename = f"payslip_{payslip.employee.employee_id}_{payslip.payroll_run.year}_{payslip.payroll_run.month:02d}.pdf"
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


@extend_schema(tags=["payroll"])
class BankTransferExportView(APIView):
    """Export bank transfer list for a payroll run as Excel."""
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def get(self, request: Request, pk: int) -> HttpResponse:
        try:
            run = PayrollRun.objects.get(pk=pk)
        except PayrollRun.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        payslips = run.payslips.select_related("employee").all()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Bank Transfer"
        ws.append(["Employee ID", "Full Name", "Bank", "Account Number", "Net Pay (ETB)"])
        for p in payslips:
            ws.append([
                p.employee.employee_id,
                p.employee.get_full_name(),
                p.employee.bank_name,
                p.employee.bank_account_number,
                float(p.net_pay),
            ])
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="bank_transfer_{run.year}_{run.month:02d}.xlsx"'
        wb.save(response)
        return response
