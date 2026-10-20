from django.contrib import admin
from employees.models import Employee, EmployeeDocument, EmployeeStatusHistory, EmploymentContract


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["employee_id", "first_name", "last_name", "department", "position", "status", "hire_date"]
    list_filter = ["status", "department", "gender"]
    search_fields = ["employee_id", "first_name", "last_name", "tin_number"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(EmploymentContract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["employee", "contract_type", "start_date", "end_date", "is_active"]
    list_filter = ["contract_type", "is_active"]


@admin.register(EmployeeDocument)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["name", "employee", "uploaded_at", "uploaded_by"]
    readonly_fields = ["uploaded_at"]


@admin.register(EmployeeStatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ["employee", "old_status", "new_status", "changed_by", "changed_at"]
    readonly_fields = ["changed_at"]
