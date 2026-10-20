import sys
print("Python:", sys.version)
results = {}
pkgs = [
    "django", "rest_framework", "rest_framework_simplejwt",
    "corsheaders", "django_filters", "drf_spectacular",
    "reportlab", "openpyxl", "decouple",
    "pytest", "faker", "factory"
]
for p in pkgs:
    try:
        m = __import__(p)
        v = getattr(m, "__version__", "ok")
        results[p] = v
    except ImportError as e:
        results[p] = f"MISSING - {e}"

for k, v in results.items():
    print(f"  {k}: {v}")
