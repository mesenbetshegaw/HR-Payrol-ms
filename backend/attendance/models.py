"""Attendance models: daily records, overtime approval."""
from django.db import models


class AttendanceStatus(models.TextChoices):
    PRESENT = "PRESENT", "Present"
    ABSENT = "ABSENT", "Absent"
    LATE = "LATE", "Late"
    HALF_DAY = "HALF_DAY", "Half Day"
    ON_LEAVE = "ON_LEAVE", "On Leave"
    HOLIDAY = "HOLIDAY", "Holiday"


class OvertimeStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class AttendanceRecord(models.Model):
    """One row per employee per day."""

    employee = models.ForeignKey(
        "employees.Employee", on_delete=models.CASCADE, related_name="attendance_records"
    )
    date = models.DateField(db_index=True)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)

    # Overtime
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_type = models.CharField(max_length=20, blank=True,
        choices=[("NORMAL", "Normal Day"), ("NIGHT", "Night"), ("REST", "Weekly Rest"), ("HOLIDAY", "Public Holiday")])
    overtime_status = models.CharField(max_length=20, choices=OvertimeStatus.choices, default=OvertimeStatus.PENDING)
    overtime_approved_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_overtimes"
    )

    # Manual entry info
    is_manual = models.BooleanField(default=False)
    manual_entry_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="manual_attendances"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("employee", "date")]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.employee} — {self.date} ({self.status})"

    @property
    def worked_hours(self):
        if self.check_in and self.check_out:
            import datetime
            ci = datetime.datetime.combine(self.date, self.check_in)
            co = datetime.datetime.combine(self.date, self.check_out)
            diff = co - ci
            return round(diff.seconds / 3600, 2)
        return 0


class MonthlySummary(models.Model):
    """Pre-computed monthly attendance summary per employee."""

    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE, related_name="monthly_summaries")
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    present_days = models.PositiveSmallIntegerField(default=0)
    absent_days = models.PositiveSmallIntegerField(default=0)
    late_days = models.PositiveSmallIntegerField(default=0)
    half_days = models.PositiveSmallIntegerField(default=0)
    total_overtime_hours = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("employee", "year", "month")]

    def __str__(self):
        return f"{self.employee} {self.year}/{self.month:02d}"
