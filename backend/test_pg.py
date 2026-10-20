"""Test PostgreSQL connection with psycopg v3."""
import psycopg

try:
    conn = psycopg.connect(
        dbname="hr_payroll_db",
        user="hr_payroll_user",
        password="8640",
        host="127.0.0.1",
        port=5432
    )
    cur = conn.execute("SELECT version()")
    row = cur.fetchone()
    print("✅ PostgreSQL connection OK!")
    print(f"   Version: {row[0]}")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
