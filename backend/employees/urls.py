from django.urls import path
from employees import views

urlpatterns = [
    path("", views.EmployeeListCreateView.as_view(), name="employee-list"),
    path("export/", views.EmployeeExportView.as_view(), name="employee-export"),
    path("<int:pk>/", views.EmployeeDetailView.as_view(), name="employee-detail"),
    path("<int:pk>/status/", views.EmployeeStatusChangeView.as_view(), name="employee-status"),
    path("<int:pk>/status-history/", views.EmployeeStatusHistoryView.as_view(), name="employee-status-history"),
    path("<int:employee_pk>/contracts/", views.ContractListCreateView.as_view(), name="contract-list"),
    path("<int:employee_pk>/contracts/<int:pk>/", views.ContractDetailView.as_view(), name="contract-detail"),
    path("<int:employee_pk>/documents/", views.DocumentListCreateView.as_view(), name="document-list"),
    path("<int:employee_pk>/documents/<int:pk>/", views.DocumentDetailView.as_view(), name="document-detail"),
]
