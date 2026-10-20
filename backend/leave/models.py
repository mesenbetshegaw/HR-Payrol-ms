"""Leave management models."""
from django.db import models


class LeaveStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    MANAGER_APPROVED = "MANAGER_APPROVED", "Manager Approved"
    APPROVED = "APPROVED", "HR Approved"
    REJECTED = "REJECTED", "Rejected"
    CANCELLED = "CANCELLED", "Cancelled"


class LeaveType(models.Model):
    """Configurable leave type (annual, sick, maternity, etc.)."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    default_days_per_year = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=True)
    requires_document = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeaveBalance(models.Model):
    """Annual leave balance per employee per leave type."""

    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE, related_name="leave_balances")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name="balances")
    year = models.PositiveSmallIntegerField()
    allocated_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    used_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    carried_over = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = [("employee", "leave_type", "year")]

    def __str__(self):
        return f"{self.employee} — {self.leave_type} ({self.year})"

    @property
    def remaining_days(self):
        return self.allocated_days + self.carried_over - self.used_days


class LeaveRequest(models.Model):
    """A leave request submitted by an employee."""

    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_days = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=LeaveStatus.choices, default=LeaveStatus.PENDING)
    document = models.FileField(upload_to="leave/documents/", null=True, blank=True)

    # Approval chain
    manager_approved_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="manager_approved_leaves"
    )
    manager_approved_at = models.DateTimeField(null=True, blank=True)
    manager_notes = models.TextField(blank=True)

    hr_approved_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="hr_approved_leaves"
    )
    hr_approved_at = models.DateTimeField(null=True, blank=True)
    hr_notes = models.TextField(blank=True)

    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee} — {self.leave_type} ({self.start_date} to {self.end_date})"
