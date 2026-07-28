from rest_framework import serializers

from .models import User


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "is_active", "is_staff", "created_at"]


class AdminUserStatusUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()
