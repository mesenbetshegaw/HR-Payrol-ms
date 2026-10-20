from django.contrib import admin
from attendance.models import AttendanceRecord, MonthlySummary


@admin.register(AttendanceRecord)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["employee", "date", "check_in", "check_out", "status", "overtime_hours", "overtime_status"]
    list_filter = ["status", "overtime_status", "date"]
    search_fields = ["employee__first_name", "employee__last_name"]
    date_hierarchy = "date"


@admin.register(MonthlySummary)
class MonthlySummaryAdmin(admin.ModelAdmin):
    list_display = ["employee", "year", "month", "present_days", "absent_days", "total_overtime_hours"]
    list_filter = ["year", "month"]
