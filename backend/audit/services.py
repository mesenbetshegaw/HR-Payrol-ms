"""Utility functions for writing audit log entries."""
from __future__ import annotations

import json
import logging
from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db import models

from audit.models import AuditAction, AuditLog

logger = logging.getLogger(__name__)


def _serialize(value: Any) -> Any:
    """Best-effort JSON-serializable conversion."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    try:
        return json.loads(json.dumps(value, default=str))
    except Exception:
        return str(value)


def log_action(
    *,
    actor,
    action: str,
    obj: models.Model | None = None,
    old_value: Any = None,
    new_value: Any = None,
    ip_address: str | None = None,
    user_agent: str = "",
    extra: dict | None = None,
) -> AuditLog:
    """Create an AuditLog entry.

    Args:
        actor: The User performing the action (can be None for system actions).
        action: One of AuditAction choices.
        obj: The Django model instance being acted upon.
        old_value: Pre-change state (dict or serializable).
        new_value: Post-change state (dict or serializable).
        ip_address: Request IP address.
        user_agent: Request User-Agent header.
        extra: Additional context dict.

    Returns:
        Created AuditLog instance.
    """
    ct = None
    object_id = None
    object_repr = ""
    if obj is not None:
        try:
            ct = ContentType.objects.get_for_model(obj)
            object_id = obj.pk
            object_repr = str(obj)[:255]
        except Exception:
            pass

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        content_type=ct,
        object_id=object_id,
        object_repr=object_repr,
        old_value=_serialize(old_value),
        new_value=_serialize(new_value),
        ip_address=ip_address,
        user_agent=user_agent[:512] if user_agent else "",
        extra=extra or {},
    )
