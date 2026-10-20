"""Root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def api_root(request):
    """Welcome page — lists all available endpoints."""
    return JsonResponse({
        "message": "Ethiopian HR & Payroll Management System API",
        "version": "1.0.0",
        "status": "running",
        "database": "PostgreSQL 18",
        "endpoints": {
            "admin_panel":   "http://127.0.0.1:8000/admin/",
            "swagger_docs":  "http://127.0.0.1:8000/api/docs/",
            "redoc_docs":    "http://127.0.0.1:8000/api/redoc/",
            "openapi_schema":"http://127.0.0.1:8000/api/schema/",
            "login":         "POST http://127.0.0.1:8000/api/v1/auth/login/",
            "register":      "POST http://127.0.0.1:8000/api/v1/auth/register/",
            "employees":     "GET  http://127.0.0.1:8000/api/v1/employees/",
            "leave":         "GET  http://127.0.0.1:8000/api/v1/leave/requests/",
            "payroll":       "GET  http://127.0.0.1:8000/api/v1/payroll/runs/",
            "attendance":    "GET  http://127.0.0.1:8000/api/v1/attendance/",
            "notifications": "GET  http://127.0.0.1:8000/api/v1/notifications/",
            "audit_logs":    "GET  http://127.0.0.1:8000/api/v1/audit/logs/",
            "dashboard":     "GET  http://127.0.0.1:8000/api/v1/reports/dashboard/admin/",
        },
        "frontend": "http://localhost:5173",
        "credentials": {
            "admin":    "messi@hrpayroll.et / 8640",
            "subadmin": "subadmin@hrpayroll.et / SubAdmin@1234",
            "manager":  "manager@hrpayroll.et / Manager@1234",
            "employee": "employee@hrpayroll.et / Employee@1234",
        }
    }, json_dumps_params={"indent": 2})


urlpatterns = [
    # Welcome / root
    path("", api_root, name="api-root"),

    path("admin/", admin.site.urls),

    # API v1
    path("api/v1/auth/",          include("accounts.urls")),
    path("api/v1/organization/",  include("organization.urls")),
    path("api/v1/employees/",     include("employees.urls")),
    path("api/v1/attendance/",    include("attendance.urls")),
    path("api/v1/leave/",         include("leave.urls")),
    path("api/v1/payroll/",       include("payroll.urls")),
    path("api/v1/reports/",       include("reports.urls")),
    path("api/v1/notifications/", include("notifications.urls")),
    path("api/v1/audit/",         include("audit.urls")),

    # OpenAPI docs
    path("api/schema/", SpectacularAPIView.as_view(),                         name="schema"),
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"),    name="swagger-ui"),
    path("api/redoc/",  SpectacularRedocView.as_view(url_name="schema"),      name="redoc"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
