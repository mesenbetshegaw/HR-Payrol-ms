from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "category", "is_read", "related_object_id", "created_at"]
        read_only_fields = ["message", "category", "related_object_id", "created_at"]
