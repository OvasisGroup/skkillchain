from rest_framework import serializers

from .models import AiChatMessage, AiChatSession


class AiChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiChatSession
        fields = ["id", "course", "context_type", "started_at", "ended_at"]


class AiChatSessionCreateSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()


class AiChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiChatMessage
        fields = ["id", "session", "role", "content", "tokens_used", "created_at"]


class AiChatMessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(allow_blank=False)
