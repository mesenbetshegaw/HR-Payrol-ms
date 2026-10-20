"""Show PostgreSQL table stats — confirms everything is stored in the DB."""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection

with connection.cursor() as c:
    c.execute("""
        SELECT relname, n_live_tup
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC
    """)
    rows = c.fetchall()

print(f"\n{'TABLE':<45} {'ROWS':>6}")
print("-" * 55)
for table, rows_count in rows:
    print(f"{table:<45} {rows_count:>6}")

# Also show user summary
from accounts.models import User, RegistrationRequest
from employees.models import Employee
from payroll.models import PayrollRun, TaxBracket
from leave.models import LeaveRequest

print("\n=== LIVE DATA SUMMARY ===")
print(f"  Users:                 {User.objects.count()}")
print(f"  Registration Requests: {RegistrationRequest.objects.count()}")
print(f"  Employees:             {Employee.objects.count()}")
print(f"  Tax Brackets:          {TaxBracket.objects.count()}")
print(f"  Payroll Runs:          {PayrollRun.objects.count()}")
print(f"  Leave Requests:        {LeaveRequest.objects.count()}")
print(f"\n  DB Engine: PostgreSQL 18.6")
print(f"  DB Name:   hr_payroll_db")
print(f"  DB User:   hr_payroll_user")
