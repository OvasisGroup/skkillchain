from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.authorization.permissions import HasPermission

from .models import AuditLog
from .serializers import AuditLogSerializer


@extend_schema(tags=["Admin"])
class AdminAuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [HasPermission]
    required_permission = "audit_logs.view"

    def get_queryset(self):
        queryset = AuditLog.objects.select_related("actor")
        action = self.request.query_params.get("action")
        if action:
            queryset = queryset.filter(action=action)
        return queryset
