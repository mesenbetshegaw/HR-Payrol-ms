from rest_framework import serializers
from audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id", "actor", "actor_email", "action", "model_name",
            "object_id", "object_repr", "old_value", "new_value",
            "ip_address", "timestamp", "extra",
        ]
        read_only_fields = fields

    def get_actor_email(self, obj):
        return obj.actor.email if obj.actor else None

    def get_model_name(self, obj):
        return obj.content_type.model if obj.content_type else None
