from rest_framework import serializers

from .models import InstructorApplication


class InstructorApplicationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = InstructorApplication
        fields = ["id", "user", "user_email", "status", "applied_at", "approved_at", "approved_by"]
