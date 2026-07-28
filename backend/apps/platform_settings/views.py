from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.authorization.permissions import HasPermission

from . import services
from .models import Setting
from .serializers import SettingSerializer, SettingUpsertSerializer


@extend_schema(tags=["Admin"])
class AdminSettingsView(APIView):
    permission_classes = [HasPermission]
    required_permission = "settings.manage"
    throttle_scope = "admin-write"

    @extend_schema(responses={200: SettingSerializer(many=True)})
    def get(self, request):
        return Response(SettingSerializer(Setting.objects.all(), many=True).data)

    @extend_schema(request=SettingUpsertSerializer, responses={200: SettingSerializer})
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
