from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.authorization.permissions import HasPermission

from . import services
from .models import Setting
from .serializers import SettingSerializer, SettingUpsertSerializer

_SETTING_EXAMPLE = {
    "id": "f1e2d3c4-...",
    "scope_type": "platform",
    "scope_id": None,
    "key": "maintenance_mode",
    "value_json": False,
    "updated_at": "2026-01-01T00:00:00Z",
}


@extend_schema(tags=["Admin"])
class AdminSettingsView(APIView):
    permission_classes = [HasPermission]
    required_permission = "settings.manage"
    throttle_scope = "admin-write"

    @extend_schema(
        responses={200: SettingSerializer(many=True)},
        description="Lists all platform/scoped settings.",
        examples=[OpenApiExample("Setting", value=_SETTING_EXAMPLE, response_only=True)],
    )
    def get(self, request):
        return Response(SettingSerializer(Setting.objects.all(), many=True).data)

    @extend_schema(
        request=SettingUpsertSerializer,
        responses={200: SettingSerializer},
        description="Creates or updates a setting by (scope_type, scope_id, key).",
        examples=[
            OpenApiExample(
                "Update setting",
                value={
                    "scope_type": "platform",
                    "key": "maintenance_mode",
                    "value_json": True,
                },
                request_only=True,
            ),
            OpenApiExample(
                "Updated",
                value={**_SETTING_EXAMPLE, "value_json": True},
                response_only=True,
            ),
        ],
    )
    def patch(self, request):
        serializer = SettingUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        setting = services.upsert_setting(**serializer.validated_data)
        record_event(
            actor=request.user,
            action="setting.update",
            entity_type="Setting",
            entity_id=setting.id,
            request=request,
            payload={"key": setting.key},
        )
        return Response(SettingSerializer(setting).data)
