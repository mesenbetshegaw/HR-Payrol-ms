from django.contrib import admin
from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "category", "is_read", "created_at", "message"]
    list_filter = ["is_read", "category"]
