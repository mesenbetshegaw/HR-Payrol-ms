from django.urls import path
from reports import views

urlpatterns = [
    path("dashboard/admin/", views.AdminDashboardView.as_view(), name="admin-dashboard"),
    path("dashboard/manager/", views.ManagerDashboardView.as_view(), name="manager-dashboard"),
    path("dashboard/employee/", views.EmployeeDashboardView.as_view(), name="employee-dashboard"),
]
