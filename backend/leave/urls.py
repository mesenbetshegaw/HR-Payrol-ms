from django.urls import path
from leave import views

urlpatterns = [
    path("types/", views.LeaveTypeListCreateView.as_view(), name="leave-type-list"),
    path("types/<int:pk>/", views.LeaveTypeDetailView.as_view(), name="leave-type-detail"),
    path("balances/", views.LeaveBalanceListView.as_view(), name="leave-balance-list"),
    path("requests/", views.LeaveRequestListCreateView.as_view(), name="leave-request-list"),
    path("requests/<int:pk>/", views.LeaveRequestDetailView.as_view(), name="leave-request-detail"),
    path("requests/<int:pk>/manager-approve/", views.ManagerApproveLeaveView.as_view(), name="leave-manager-approve"),
    path("requests/<int:pk>/hr-approve/", views.HRApproveLeaveView.as_view(), name="leave-hr-approve"),
    path("requests/<int:pk>/reject/", views.RejectLeaveView.as_view(), name="leave-reject"),
    path("requests/<int:pk>/cancel/", views.CancelLeaveView.as_view(), name="leave-cancel"),
    path("calendar/", views.LeaveCalendarView.as_view(), name="leave-calendar"),
]
