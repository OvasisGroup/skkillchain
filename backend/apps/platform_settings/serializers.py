from rest_framework import serializers

from .models import Setting


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ["id", "scope_type", "scope_id", "key", "value_json", "updated_at"]


class SettingUpsertSerializer(serializers.Serializer):
    scope_type = serializers.ChoiceField(choices=Setting.SCOPE_CHOICES, default=Setting.SCOPE_PLATFORM)
    scope_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    key = serializers.CharField(max_length=150)
    value_json = serializers.JSONField()
