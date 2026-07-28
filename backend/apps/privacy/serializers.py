from rest_framework import serializers

from .models import DataErasureRequest, LegalHold


class DataErasureRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = DataErasureRequest
        fields = [
            "id",
            "user",
            "user_email",
            "status",
            "block_reason",
            "requested_at",
            "completed_at",
        ]
        read_only_fields = fields


class LegalHoldSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalHold
        fields = ["id", "user", "reason", "created_at", "released_at"]
        read_only_fields = fields


class LegalHoldCreateSerializer(serializers.Serializer):
    reason = serializers.CharField()
