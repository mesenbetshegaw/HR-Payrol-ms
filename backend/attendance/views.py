from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserRole
from accounts.permissions import IsAdminOrSubAdmin, IsManager
from attendance import services
from attendance.models import AttendanceRecord, MonthlySummary
from attendance.serializers import (
    AttendanceRecordSerializer, CheckInSerializer, CheckOutSerializer, MonthlySummarySerializer
)


@extend_schema(tags=["attendance"])
class AttendanceListView(generics.ListCreateAPIView):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    filterset_fields = ["employee", "status", "date", "overtime_status"]
    search_fields = ["employee__first_name", "employee__last_name"]
    ordering = ["-date"]

    def get_queryset(self):
        qs = AttendanceRecord.objects.select_related("employee", "overtime_approved_by")
        user = self.request.user
        if user.role == UserRole.MANAGER and user.managed_department:
            qs = qs.filter(employee__department=user.managed_department)
        elif user.role == UserRole.EMPLOYEE and hasattr(user, "employee"):
            qs = qs.filter(employee=user.employee)
        return qs


@extend_schema(tags=["attendance"])
class AttendanceDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def get_queryset(self):
        return AttendanceRecord.objects.select_related("employee")


@extend_schema(tags=["attendance"])
class CheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        s = CheckInSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        is_manual = request.user.role in (UserRole.ADMIN, UserRole.SUB_ADMIN)
        record = services.check_in(
            employee_id=d["employee_id"],
            date=d["date"],
            check_in_time=d["check_in"],
            notes=d.get("notes", ""),
            is_manual=is_manual,
            actor=request.user if is_manual else None,
        )
        return Response(AttendanceRecordSerializer(record).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["attendance"])
class CheckOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        try:
            record = AttendanceRecord.objects.get(pk=pk)
        except AttendanceRecord.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        s = CheckOutSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        record = services.check_out(record, d["check_out"], d.get("overtime_hours", 0), d.get("overtime_type", ""))
        return Response(AttendanceRecordSerializer(record).data)


@extend_schema(tags=["attendance"])
class OvertimeApprovalView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def post(self, request: Request, pk: int) -> Response:
        try:
            record = AttendanceRecord.objects.select_related("employee__department").get(pk=pk)
        except AttendanceRecord.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        # Manager can only approve their department
        if request.user.role == UserRole.MANAGER:
            if record.employee.department != request.user.managed_department:
                return Response({"detail": "Not your department."}, status=403)
        action = request.data.get("action", "approve")
        if action == "approve":
            services.approve_overtime(record, request.user)
        else:
            record.overtime_status = "REJECTED"
            record.save(update_fields=["overtime_status"])
        return Response(AttendanceRecordSerializer(record).data)


@extend_schema(tags=["attendance"])
class MonthlySummaryView(generics.ListAPIView):
    serializer_class = MonthlySummarySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["employee", "year", "month"]

    def get_queryset(self):
        qs = MonthlySummary.objects.select_related("employee")
        user = self.request.user
        if user.role == UserRole.EMPLOYEE and hasattr(user, "employee"):
            qs = qs.filter(employee=user.employee)
        elif user.role == UserRole.MANAGER and user.managed_department:
            qs = qs.filter(employee__department=user.managed_department)
        return qs


@extend_schema(tags=["attendance"])
class GenerateMonthlySummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def post(self, request: Request) -> Response:
        employee_id = request.data.get("employee_id")
        year = request.data.get("year")
        month = request.data.get("month")
        if not all([employee_id, year, month]):
            return Response({"detail": "employee_id, year, month required."}, status=400)
        summary = services.compute_monthly_summary(int(employee_id), int(year), int(month))
        return Response(MonthlySummarySerializer(summary).data)
