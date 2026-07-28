from rest_framework import serializers

from .models import ConferencingAccount, LiveSession, LiveSessionRecording, LiveSessionRegistration


class ConferencingAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConferencingAccount
        # access_token_encrypted / refresh_token_encrypted deliberately
        # never appear here — see the M4 live_sessions commit notes.
        fields = ["id", "provider", "external_account_id", "connected_at", "revoked_at"]


class ConnectResponseSerializer(serializers.Serializer):
    authorization_url = serializers.CharField()


class LiveSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveSession
        fields = [
            "id",
            "course",
            "provider",
            "title",
            "description",
            "scheduled_start_at",
            "scheduled_end_at",
            "timezone",
            "status",
            "capacity",
            "is_recorded",
        ]


class LiveSessionCreateSerializer(serializers.ModelSerializer):
    conferencing_account_id = serializers.UUIDField()

    class Meta:
        model = LiveSession
        fields = [
            "conferencing_account_id",
            "provider",
            "title",
            "description",
            "scheduled_start_at",
            "scheduled_end_at",
            "timezone",
            "capacity",
            "is_recorded",
        ]

    def validate(self, attrs):
        if attrs["scheduled_end_at"] <= attrs["scheduled_start_at"]:
            raise serializers.ValidationError("scheduled_end_at must be after scheduled_start_at.")
        return attrs


class LiveSessionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveSession
        fields = [
            "title",
            "description",
            "scheduled_start_at",
            "scheduled_end_at",
            "timezone",
            "capacity",
        ]


class RegistrationSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.email", read_only=True)

    class Meta:
        model = LiveSessionRegistration
        fields = [
            "id",
            "student_email",
            "status",
            "registered_at",
            "joined_at",
            "left_at",
            "attended_duration_seconds",
        ]


class JoinResponseSerializer(serializers.Serializer):
    join_url = serializers.URLField()


class RecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveSessionRecording
        fields = ["playback_url", "duration_seconds", "available_at"]
