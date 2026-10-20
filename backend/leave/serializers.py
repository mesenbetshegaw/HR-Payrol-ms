from rest_framework import serializers
from leave.models import LeaveBalance, LeaveRequest, LeaveType


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ["id", "name", "code", "default_days_per_year", "is_paid", "requires_document", "is_active", "description"]


class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)
    remaining_days = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = ["id", "employee", "employee_name", "leave_type", "leave_type_name", "year",
                  "allocated_days", "used_days", "carried_over", "remaining_days"]
        read_only_fields = ["remaining_days"]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)
    manager_approved_by_name = serializers.SerializerMethodField()
    hr_approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            "id", "employee", "employee_name", "leave_type", "leave_type_name",
            "start_date", "end_date", "number_of_days", "reason", "status", "document",
            "manager_approved_by", "manager_approved_by_name", "manager_approved_at", "manager_notes",
            "hr_approved_by", "hr_approved_by_name", "hr_approved_at", "hr_notes",
            "rejection_reason", "created_at", "updated_at",
        ]
        read_only_fields = [
            "status", "manager_approved_by", "manager_approved_by_name", "manager_approved_at",
            "hr_approved_by", "hr_approved_by_name", "hr_approved_at", "rejection_reason",
            "created_at", "updated_at",
        ]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()

    def get_manager_approved_by_name(self, obj):
        return obj.manager_approved_by.get_full_name() if obj.manager_approved_by else None

    def get_hr_approved_by_name(self, obj):
        return obj.hr_approved_by.get_full_name() if obj.hr_approved_by else None


class LeaveApprovalSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class LeaveRejectionSerializer(serializers.Serializer):
    reason = serializers.CharField()


class LeaveCalendarSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = ["id", "employee_name", "leave_type_name", "start_date", "end_date", "status"]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()
