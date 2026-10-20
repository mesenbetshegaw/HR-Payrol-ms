"""Employee views."""
from __future__ import annotations

import openpyxl
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminOrSubAdmin, IsSameDepartment, IsManager
from accounts.models import UserRole
from employees import services
from employees.models import Employee, EmployeeDocument, EmployeeStatusHistory, EmploymentContract
from employees.serializers import (
    EmployeeDocumentSerializer,
    EmployeeListSerializer,
    EmployeeSerializer,
    EmployeeStatusHistorySerializer,
    EmploymentContractSerializer,
)


@extend_schema(tags=["employees"])
class EmployeeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    filterset_fields = ["department", "status", "position", "branch"]
    search_fields = ["first_name", "last_name", "employee_id", "tin_number"]
    ordering_fields = ["hire_date", "last_name", "employee_id"]
    ordering = ["last_name"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EmployeeSerializer
        return EmployeeListSerializer

    def get_queryset(self):
        qs = Employee.objects.select_related("department", "position", "branch")
        user = self.request.user
        if user.role == UserRole.MANAGER and user.managed_department:
            qs = qs.filter(department=user.managed_department)
        return qs

    def perform_create(self, serializer):
        services.create_employee(serializer.validated_data)

    def create(self, request, *args, **kwargs):
        serializer = EmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = services.create_employee(serializer.validated_data)
        return Response(EmployeeSerializer(employee).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["employees"])
class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsManager]
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        return Employee.objects.select_related("department", "position", "branch").prefetch_related("contracts")

    def perform_update(self, serializer):
        services.update_employee(self.get_object(), serializer.validated_data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        employee = self.get_object()
        serializer = EmployeeSerializer(employee, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = services.update_employee(employee, serializer.validated_data)
        return Response(EmployeeSerializer(updated).data)

    def destroy(self, request, *args, **kwargs):
        employee = self.get_object()
        services.change_employee_status(employee, "TERMINATED", "Deleted via API", request.user)
        return Response({"detail": "Employee terminated."}, status=status.HTTP_200_OK)


@extend_schema(tags=["employees"])
class EmployeeStatusChangeView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def post(self, request: Request, pk: int) -> Response:
        try:
            employee = Employee.objects.get(pk=pk)
        except Employee.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        new_status = request.data.get("status")
        reason = request.data.get("reason", "")
        if new_status not in [s.value for s in EmploymentContract.DoesNotExist.__class__.__mro__]:
            pass  # validated below
        from employees.models import EmploymentStatus
        valid = [s[0] for s in EmploymentStatus.choices]
        if new_status not in valid:
            return Response({"detail": f"Invalid status. Choose from {valid}"}, status=400)
        services.change_employee_status(employee, new_status, reason, request.user)
        return Response(EmployeeSerializer(employee).data)


@extend_schema(tags=["employees"])
class EmployeeStatusHistoryView(generics.ListAPIView):
    serializer_class = EmployeeStatusHistorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def get_queryset(self):
        return EmployeeStatusHistory.objects.filter(
            employee_id=self.kwargs["pk"]
        ).select_related("changed_by")


@extend_schema(tags=["employees"])
class ContractListCreateView(generics.ListCreateAPIView):
    serializer_class = EmploymentContractSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def get_queryset(self):
        return EmploymentContract.objects.filter(employee_id=self.kwargs["employee_pk"])

    def perform_create(self, serializer):
        serializer.save(employee_id=self.kwargs["employee_pk"])


@extend_schema(tags=["employees"])
class ContractDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmploymentContractSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def get_queryset(self):
        return EmploymentContract.objects.filter(employee_id=self.kwargs["employee_pk"])


@extend_schema(tags=["employees"])
class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return EmployeeDocument.objects.filter(employee_id=self.kwargs["employee_pk"])

    def perform_create(self, serializer):
        from django.conf import settings
        file = self.request.FILES.get("file")
        if file and file.size > settings.MAX_UPLOAD_SIZE_BYTES:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"file": f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB."})
        serializer.save(employee_id=self.kwargs["employee_pk"], uploaded_by=self.request.user)


@extend_schema(tags=["employees"])
class DocumentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def get_queryset(self):
        return EmployeeDocument.objects.filter(employee_id=self.kwargs["employee_pk"])


@extend_schema(tags=["employees"])
class EmployeeExportView(APIView):
    """Export employees to CSV or Excel."""
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def get(self, request: Request) -> HttpResponse:
        fmt = request.query_params.get("format", "csv")
        qs = Employee.objects.select_related("department", "position")

        if fmt == "xlsx":
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Employees"
            headers = ["Employee ID", "First Name", "Last Name", "Department", "Position", "Status", "Hire Date"]
            ws.append(headers)
            for emp in qs:
                ws.append([
                    emp.employee_id, emp.first_name, emp.last_name,
                    emp.department.name if emp.department else "",
                    emp.position.name if emp.position else "",
                    emp.status, str(emp.hire_date),
                ])
            response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response["Content-Disposition"] = 'attachment; filename="employees.xlsx"'
            wb.save(response)
            return response

        csv_data = services.export_employees_csv(qs)
        response = HttpResponse(csv_data, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="employees.csv"'
        return response
