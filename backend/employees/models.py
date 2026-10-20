"""Employee models: profile, contract, document, status history."""
from django.core.validators import FileExtensionValidator
from django.db import models


class Gender(models.TextChoices):
    MALE = "M", "Male"
    FEMALE = "F", "Female"
    OTHER = "O", "Other"


class EmploymentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    TERMINATED = "TERMINATED", "Terminated"
    ON_LEAVE = "ON_LEAVE", "On Leave"


class ContractType(models.TextChoices):
    PERMANENT = "PERMANENT", "Permanent"
    CONTRACT = "CONTRACT", "Contract"
    PART_TIME = "PART_TIME", "Part Time"
    INTERN = "INTERN", "Intern"


def employee_document_path(instance, filename):
    return f"employees/{instance.employee.employee_id}/documents/{filename}"


class Employee(models.Model):
    """Core employee profile."""

    employee_id = models.CharField(max_length=20, unique=True, db_index=True)

    # Personal info
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    amharic_name = models.CharField(max_length=200, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    nationality = models.CharField(max_length=100, default="Ethiopian")
    phone_number = models.CharField(max_length=20, blank=True)
    personal_email = models.EmailField(blank=True)

    # Tax & pension
    tin_number = models.CharField(max_length=50, blank=True, verbose_name="TIN Number")
    pension_number = models.CharField(max_length=50, blank=True)

    # Bank
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)

    # Emergency contact
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)

    # Org
    department = models.ForeignKey(
        "organization.Department", on_delete=models.SET_NULL, null=True, related_name="employees"
    )
    position = models.ForeignKey(
        "organization.Position", on_delete=models.SET_NULL, null=True, related_name="employees"
    )
    branch = models.ForeignKey(
        "organization.Branch", on_delete=models.SET_NULL, null=True, blank=True, related_name="employees"
    )

    # Status
    status = models.CharField(max_length=20, choices=EmploymentStatus.choices, default=EmploymentStatus.ACTIVE)
    hire_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)

    profile_picture = models.FileField(upload_to="employees/photos/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def years_of_service(self) -> float:
        from django.utils import timezone
        import datetime
        end = self.termination_date or timezone.now().date()
        delta = end - self.hire_date
        return delta.days / 365.25


class EmploymentContract(models.Model):
    """Employment contract linked to an employee."""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="contracts")
    contract_type = models.CharField(max_length=20, choices=ContractType.choices)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.employee} — {self.contract_type}"


class EmployeeDocument(models.Model):
    """Uploaded document for an employee."""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=200)
    file = models.FileField(
        upload_to=employee_document_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"])],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="uploaded_documents"
    )

    def __str__(self):
        return f"{self.name} — {self.employee}"


class EmployeeStatusHistory(models.Model):
    """Tracks status changes for an employee."""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="status_history")
    old_status = models.CharField(max_length=20, choices=EmploymentStatus.choices)
    new_status = models.CharField(max_length=20, choices=EmploymentStatus.choices)
    changed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="status_changes"
    )
    reason = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.employee} {self.old_status}→{self.new_status}"
