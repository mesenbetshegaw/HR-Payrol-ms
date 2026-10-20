from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdminOrSubAdmin
from organization.models import Branch, Department, Position, PublicHoliday
from organization.serializers import (
    BranchSerializer, DepartmentSerializer, PositionSerializer, PublicHolidaySerializer
)


@extend_schema(tags=["organization"])
class DepartmentListCreateView(generics.ListCreateAPIView):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    filterset_fields = ["is_active", "parent"]
    search_fields = ["name", "code"]
    ordering = ["name"]

    def get_permissions(self):
        # Anyone can list departments (needed for registration form)
        if self.request.method == "GET":
            return []
        return super().get_permissions()

    def get_queryset(self):
        return Department.objects.prefetch_related("children").all()


@extend_schema(tags=["organization"])
class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    queryset = Department.objects.all()


@extend_schema(tags=["organization"])
class PositionListCreateView(generics.ListCreateAPIView):
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    filterset_fields = ["department", "is_active"]
    search_fields = ["name", "grade"]

    def get_permissions(self):
        # Anyone can list positions (needed for registration form)
        if self.request.method == "GET":
            return []
        return super().get_permissions()

    def get_queryset(self):
        return Position.objects.select_related("department").all()


@extend_schema(tags=["organization"])
class PositionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    queryset = Position.objects.select_related("department").all()


@extend_schema(tags=["organization"])
class BranchListCreateView(generics.ListCreateAPIView):
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    filterset_fields = ["is_active"]
    search_fields = ["name", "city"]
    queryset = Branch.objects.all()


@extend_schema(tags=["organization"])
class BranchDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    queryset = Branch.objects.all()


@extend_schema(tags=["organization"])
class PublicHolidayListCreateView(generics.ListCreateAPIView):
    serializer_class = PublicHolidaySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["holiday_type"]
    search_fields = ["name"]
    ordering = ["date"]
    queryset = PublicHoliday.objects.all()


@extend_schema(tags=["organization"])
class PublicHolidayDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PublicHolidaySerializer
    permission_classes = [IsAuthenticated, IsAdminOrSubAdmin]
    queryset = PublicHoliday.objects.all()
