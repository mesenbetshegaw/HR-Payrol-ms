from rest_framework import serializers
from organization.models import Branch, Department, Position, PublicHoliday


class DepartmentSerializer(serializers.ModelSerializer):
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["id", "name", "code", "parent", "description", "is_active", "children_count", "created_at"]

    def get_children_count(self, obj):
        return obj.children.count()


class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Position
        fields = ["id", "name", "grade", "department", "department_name", "is_active", "created_at"]


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "city", "address", "is_active", "created_at"]


class PublicHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHoliday
        fields = ["id", "name", "date", "holiday_type", "is_recurring", "created_at"]
