"""Diagnose what Django's postgresql backend detects."""
import sys
print("Python:", sys.version)

# Check what Django's postgresql backend imports
try:
    from django.db.backends.postgresql.base import Database
    print("Django postgres Database:", Database)
except Exception as e:
    print("Import error:", e)

# Check if Django 5.1 supports psycopg3 natively
try:
    import django.db.backends.postgresql.psycopg_any as pa
    print("psycopg_any module found:", pa)
    print("is_psycopg3:", getattr(pa, 'is_psycopg3', 'N/A'))
except Exception as e:
    print("psycopg_any:", e)

# Try forcing psycopg3
try:
    import psycopg
    print("psycopg v3 version:", psycopg.__version__)
    print("psycopg3 available: YES")
except ImportError:
    print("psycopg3: NOT installed")

try:
    import psycopg2
    print("psycopg2 version:", psycopg2.__version__)
    print("psycopg2 available: YES")
except ImportError:
    print("psycopg2: NOT installed")
