"""Audit log model — records every create/update/delete/approve action."""
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditAction(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    DELETE = "DELETE", "Delete"
    APPROVE = "APPROVE", "Approve"
    REJECT = "REJECT", "Reject"
    LOGIN = "LOGIN", "Login"
    LOGOUT = "LOGOUT", "Logout"
    EXPORT = "EXPORT", "Export"


class AuditLog(models.Model):
    """Immutable audit trail entry."""

    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=AuditAction.choices)

    # Generic FK to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    object_repr = models.CharField(max_length=255, blank=True)

    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=["actor", "timestamp"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self) -> str:
        actor_str = self.actor.email if self.actor else "system"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {actor_str} {self.action} {self.object_repr}"
