"""Organization structure models: Department, Position, Branch, PublicHoliday."""
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True)
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Position(models.Model):
    """Job title / position."""

    name = models.CharField(max_length=150)
    grade = models.CharField(max_length=50, blank=True)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="positions"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("name", "department")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.department.name})"


class Branch(models.Model):
    name = models.CharField(max_length=150, unique=True)
    city = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.name} — {self.city}"


class HolidayType(models.TextChoices):
    NATIONAL = "NATIONAL", "National"
    RELIGIOUS = "RELIGIOUS", "Religious"
    REGIONAL = "REGIONAL", "Regional"


class PublicHoliday(models.Model):
    name = models.CharField(max_length=150)
    date = models.DateField(db_index=True)
    holiday_type = models.CharField(max_length=20, choices=HolidayType.choices, default=HolidayType.NATIONAL)
    is_recurring = models.BooleanField(default=True, help_text="Same date every year")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]
        unique_together = [("name", "date")]

    def __str__(self):
        return f"{self.name} ({self.date})"
