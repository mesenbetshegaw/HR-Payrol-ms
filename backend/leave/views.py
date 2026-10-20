from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserRole
from accounts.permissions import IsAdminOrSubAdmin, IsManager
from leave import services
from leave.models import LeaveBalance, LeaveRequest, LeaveStatus, LeaveType
from leave.serializers import (
    LeaveApprovalSerializer, LeaveBalanceSerializer, LeaveCalendarSerializer,
    LeaveRejectionSerializer, LeaveRequestSerializer, LeaveTypeSerializer,
)


@extend_schema(tags=["leave"])
class LeaveTypeListCreateView(generics.ListCreateAPIView):
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    queryset = LeaveType.objects.all()


@extend_schema(tags=["leave"])
class LeaveTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    queryset = LeaveType.objects.all()


@extend_schema(tags=["leave"])
class LeaveBalanceListView(generics.ListAPIView):
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["employee", "leave_type", "year"]

    def get_queryset(self):
        qs = LeaveBalance.objects.select_related("employee", "leave_type")
        user = self.request.user
        if user.role == UserRole.EMPLOYEE and hasattr(user, "employee"):
            qs = qs.filter(employee=user.employee)
        elif user.role == UserRole.MANAGER and user.managed_department:
            qs = qs.filter(employee__department=user.managed_department)
        return qs


@extend_schema(tags=["leave"])
class LeaveRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "leave_type", "employee"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = LeaveRequest.objects.select_related(
            "employee", "leave_type", "manager_approved_by", "hr_approved_by"
        )
        user = self.request.user
        if user.role == UserRole.EMPLOYEE and hasattr(user, "employee"):
            qs = qs.filter(employee=user.employee)
        elif user.role == UserRole.MANAGER and user.managed_department:
            qs = qs.filter(employee__department=user.managed_department)
        return qs

    def create(self, request, *args, **kwargs):
        s = LeaveRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        leave_req = services.submit_leave_request(
            employee=d["employee"],
            leave_type=d["leave_type"],
            start_date=d["start_date"],
            end_date=d["end_date"],
            number_of_days=d["number_of_days"],
            reason=d.get("reason", ""),
            document=d.get("document"),
        )
        return Response(LeaveRequestSerializer(leave_req).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["leave"])
class LeaveRequestDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LeaveRequest.objects.select_related("employee", "leave_type")


@extend_schema(tags=["leave"])
class ManagerApproveLeaveView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def post(self, request: Request, pk: int) -> Response:
        try:
            leave_req = LeaveRequest.objects.select_related("employee").get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        s = LeaveApprovalSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        leave_req = services.manager_approve_leave(leave_req, request.user, s.validated_data.get("notes", ""))
        return Response(LeaveRequestSerializer(leave_req).data)


@extend_schema(tags=["leave"])
class HRApproveLeaveView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]

    def post(self, request: Request, pk: int) -> Response:
        try:
            leave_req = LeaveRequest.objects.select_related("employee", "leave_type").get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        s = LeaveApprovalSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        leave_req = services.hr_approve_leave(leave_req, request.user, s.validated_data.get("notes", ""))
        return Response(LeaveRequestSerializer(leave_req).data)


@extend_schema(tags=["leave"])
class RejectLeaveView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def post(self, request: Request, pk: int) -> Response:
        try:
            leave_req = LeaveRequest.objects.select_related("employee").get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        s = LeaveRejectionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        leave_req = services.reject_leave(leave_req, request.user, s.validated_data["reason"])
        return Response(LeaveRequestSerializer(leave_req).data)


@extend_schema(tags=["leave"])
class CancelLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        try:
            leave_req = LeaveRequest.objects.get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        user = request.user
        # Employee can cancel their own, Admin/SubAdmin can cancel any
        if user.role == UserRole.EMPLOYEE:
            if not hasattr(user, "employee") or leave_req.employee != user.employee:
                return Response({"detail": "Forbidden."}, status=403)
        services.cancel_leave(leave_req, user)
        return Response(LeaveRequestSerializer(leave_req).data)


@extend_schema(tags=["leave"])
class LeaveCalendarView(generics.ListAPIView):
    serializer_class = LeaveCalendarSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")
        qs = LeaveRequest.objects.filter(
            status=LeaveStatus.APPROVED
        ).select_related("employee", "leave_type")
        if year:
            qs = qs.filter(start_date__year=year)
        if month:
            qs = qs.filter(start_date__month=month)
        user = self.request.user
        if user.role == UserRole.EMPLOYEE and hasattr(user, "employee"):
            qs = qs.filter(employee=user.employee)
        elif user.role == UserRole.MANAGER and user.managed_department:
            qs = qs.filter(employee__department=user.managed_department)
        return qs
