from rest_framework import serializers

from .models import Profile, User


class AdminProfileSerializer(serializers.ModelSerializer):
    # Same split as ProfileSerializer (serializers.py) — avatar travels
    # through the dedicated POST .../avatar/ endpoint, never this JSON body.
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            "first_name",
            "last_name",
            "bio",
            "avatar",
            "locale",
            "timezone",
            "linkedin_url",
            "twitter_url",
            "github_url",
            "youtube_url",
            "website_url",
        ]


class AdminUserSerializer(serializers.ModelSerializer):
    profile = AdminProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "is_active", "is_staff", "created_at", "profile"]


class AdminUserStatusUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()


class AdminAvatarUploadSerializer(serializers.Serializer):
    avatar = serializers.ImageField()
