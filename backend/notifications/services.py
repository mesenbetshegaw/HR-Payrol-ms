"""Notification creation service."""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


def notify(*, recipient, message: str, category: str = "general", related_object_id: int | None = None) -> None:
    """Create an in-app notification.

    Args:
        recipient: User to notify (can be None for broadcast).
        message: Notification message.
        category: Category tag (leave, payroll, attendance, etc.).
        related_object_id: PK of the related object for deep-linking.
    """
    if recipient is None:
        return
    try:
        from notifications.models import Notification
        Notification.objects.create(
            recipient=recipient,
            message=message,
            category=category,
            related_object_id=related_object_id,
        )
    except Exception as e:
        logger.warning("Failed to create notification: %s", e)
