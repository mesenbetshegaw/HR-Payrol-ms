from django.urls import path
from notifications import views

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="notification-list"),
    path("unread-count/", views.NotificationUnreadCountView.as_view(), name="notification-unread"),
    path("mark-all-read/", views.NotificationMarkAllReadView.as_view(), name="notification-mark-all"),
    path("<int:pk>/read/", views.NotificationMarkReadView.as_view(), name="notification-read"),
]
