from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdmin
from audit.models import AuditLog
from audit.serializers import AuditLogSerializer


@extend_schema(tags=["audit"])
class AuditLogListView(generics.ListAPIView):
    """Read-only audit log. Admin only."""

    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AuditLogSerializer
    filterset_fields = ["action", "actor"]
    search_fields = ["object_repr", "actor__email"]
    ordering_fields = ["timestamp"]
    ordering = ["-timestamp"]

    def get_queryset(self):
        return AuditLog.objects.select_related("actor", "content_type").all()
