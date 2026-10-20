from rest_framework import serializers
from employees.models import Employee, EmploymentContract, EmployeeDocument, EmployeeStatusHistory


class EmploymentContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentContract
        fields = ["id", "contract_type", "start_date", "end_date", "is_active", "notes", "created_at"]


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = ["id", "name", "file", "uploaded_at", "uploaded_by"]
        read_only_fields = ["uploaded_at", "uploaded_by"]


class EmployeeStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeStatusHistory
        fields = ["id", "old_status", "new_status", "changed_by", "changed_by_name", "reason", "changed_at"]
        read_only_fields = fields

    def get_changed_by_name(self, obj):
        return obj.changed_by.get_full_name() if obj.changed_by else None


class EmployeeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    department_name = serializers.CharField(source="department.name", read_only=True)
    position_name = serializers.CharField(source="position.name", read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            "id", "employee_id", "full_name", "first_name", "last_name",
            "department_name", "position_name", "status", "hire_date", "profile_picture",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()


class EmployeeSerializer(serializers.ModelSerializer):
    """Full employee serializer."""
    contracts = EmploymentContractSerializer(many=True, read_only=True)
    years_of_service = serializers.FloatField(read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    position_name = serializers.CharField(source="position.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id", "employee_id", "first_name", "last_name", "amharic_name",
            "date_of_birth", "gender", "nationality", "phone_number", "personal_email",
            "tin_number", "pension_number", "bank_name", "bank_account_number",
            "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relation",
            "department", "department_name", "position", "position_name", "branch", "branch_name",
            "status", "hire_date", "termination_date", "profile_picture",
            "years_of_service", "contracts", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "years_of_service"]
