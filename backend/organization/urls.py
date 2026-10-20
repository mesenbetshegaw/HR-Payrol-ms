from django.urls import path
from organization import views

urlpatterns = [
    path("departments/", views.DepartmentListCreateView.as_view(), name="dept-list"),
    path("departments/<int:pk>/", views.DepartmentDetailView.as_view(), name="dept-detail"),
    path("positions/", views.PositionListCreateView.as_view(), name="position-list"),
    path("positions/<int:pk>/", views.PositionDetailView.as_view(), name="position-detail"),
    path("branches/", views.BranchListCreateView.as_view(), name="branch-list"),
    path("branches/<int:pk>/", views.BranchDetailView.as_view(), name="branch-detail"),
    path("holidays/", views.PublicHolidayListCreateView.as_view(), name="holiday-list"),
    path("holidays/<int:pk>/", views.PublicHolidayDetailView.as_view(), name="holiday-detail"),
]
