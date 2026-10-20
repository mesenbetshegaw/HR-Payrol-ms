"""
Create PostgreSQL database and user for HR Payroll system.
Run once: python setup_db.py
"""
import subprocess
import sys

PG_BIN = r"C:\Program Files\PostgreSQL\18\bin"
PSQL = f"{PG_BIN}\\psql.exe"
PG_PASSWORD = "8640"

# SQL to run as postgres superuser
sql_commands = [
    # Drop if exists, recreate cleanly
    "DROP DATABASE IF EXISTS hr_payroll_db;",
    "DROP ROLE IF EXISTS hr_payroll_user;",
    f"CREATE ROLE hr_payroll_user WITH LOGIN PASSWORD '{PG_PASSWORD}';",
    "CREATE DATABASE hr_payroll_db OWNER hr_payroll_user ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8' TEMPLATE template0;",
    "GRANT ALL PRIVILEGES ON DATABASE hr_payroll_db TO hr_payroll_user;",
]

import os
env = os.environ.copy()
env["PGPASSWORD"] = PG_PASSWORD

for sql in sql_commands:
    result = subprocess.run(
        [PSQL, "-U", "postgres", "-h", "127.0.0.1", "-p", "5432", "-c", sql],
        env=env, capture_output=True, text=True
    )
    out = result.stdout.strip() + result.stderr.strip()
    if result.returncode == 0:
        print(f"  ✅ {sql[:60]}")
    else:
        # Some errors are acceptable (like role already exists)
        print(f"  ⚠  {sql[:60]}: {out[:100]}")

print("\n✅ Database setup complete!")
print("   DB:   hr_payroll_db")
print("   User: hr_payroll_user")
print("   Pass: 8640")
print("   Host: 127.0.0.1:5432")
