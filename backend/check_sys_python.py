import sys
print("Python:", sys.version)
print("Executable:", sys.executable)

pkgs = ["django", "rest_framework", "rest_framework_simplejwt", 
        "corsheaders", "django_filters", "drf_spectacular",
        "reportlab", "openpyxl", "decouple", "psycopg"]
for p in pkgs:
    try:
        m = __import__(p)
        v = getattr(m, "__version__", getattr(m, "VERSION", "ok"))
        print(f"  ✅ {p}: {v}")
    except ImportError as e:
        print(f"  ❌ {p}: MISSING")
