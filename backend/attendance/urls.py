from django.urls import path
from attendance import views

urlpatterns = [
    path("", views.AttendanceListView.as_view(), name="attendance-list"),
    path("<int:pk>/", views.AttendanceDetailView.as_view(), name="attendance-detail"),
    path("check-in/", views.CheckInView.as_view(), name="attendance-checkin"),
    path("<int:pk>/check-out/", views.CheckOutView.as_view(), name="attendance-checkout"),
    path("<int:pk>/overtime-approval/", views.OvertimeApprovalView.as_view(), name="overtime-approval"),
    path("summary/", views.MonthlySummaryView.as_view(), name="attendance-summary"),
    path("summary/generate/", views.GenerateMonthlySummaryView.as_view(), name="summary-generate"),
]
