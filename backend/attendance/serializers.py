from rest_framework import serializers
from attendance.models import AttendanceRecord, MonthlySummary


class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    worked_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            "id", "employee", "employee_name", "date", "check_in", "check_out",
            "status", "worked_hours", "overtime_hours", "overtime_type",
            "overtime_status", "overtime_approved_by", "is_manual", "notes",
            "created_at",
        ]
        read_only_fields = ["overtime_status", "overtime_approved_by", "created_at", "worked_hours"]

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()


class CheckInSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    date = serializers.DateField()
    check_in = serializers.TimeField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CheckOutSerializer(serializers.Serializer):
    check_out = serializers.TimeField()
    overtime_hours = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=0)
    overtime_type = serializers.ChoiceField(
        choices=["NORMAL", "NIGHT", "REST", "HOLIDAY"], required=False, allow_blank=True, default=""
    )


class MonthlySummarySerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = MonthlySummary
        fields = [
            "id", "employee", "employee_name", "year", "month",
            "present_days", "absent_days", "late_days", "half_days",
            "total_overtime_hours", "generated_at",
        ]
        read_only_fields = fields

    def get_employee_name(self, obj):
        return obj.employee.get_full_name()
