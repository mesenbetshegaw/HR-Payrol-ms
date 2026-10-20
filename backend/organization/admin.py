from django.contrib import admin
from organization.models import Branch, Department, Position, PublicHoliday


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "parent", "is_active"]
    search_fields = ["name", "code"]
    list_filter = ["is_active"]


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ["name", "grade", "department", "is_active"]
    list_filter = ["department", "is_active"]
    search_fields = ["name"]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "is_active"]
    list_filter = ["is_active"]


@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ["name", "date", "holiday_type", "is_recurring"]
    list_filter = ["holiday_type"]
