from django.contrib import admin
from leave.models import LeaveBalance, LeaveRequest, LeaveType


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "default_days_per_year", "is_paid", "is_active"]


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ["employee", "leave_type", "year", "allocated_days", "used_days"]
    list_filter = ["year", "leave_type"]


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ["employee", "leave_type", "start_date", "end_date", "number_of_days", "status"]
    list_filter = ["status", "leave_type"]
    search_fields = ["employee__first_name", "employee__last_name"]
    date_hierarchy = "start_date"
