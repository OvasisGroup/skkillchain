from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Profile

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        value = User.objects.normalize_email(value)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class TokenPairSerializer(serializers.Serializer):
    """Response shape only — mirrors SimpleJWT's own token pair output so
    OAuth login and password login return identically-shaped tokens."""

    access = serializers.CharField()
    refresh = serializers.CharField()


class OAuthTokenSerializer(serializers.Serializer):
    token = serializers.CharField(
        help_text="ID token (Google/Apple) or access token (Facebook) from the provider's own SDK."
    )


class MFAEnrollResponseSerializer(serializers.Serializer):
    provisioning_uri = serializers.CharField()
    secret = serializers.CharField(
        help_text="For manual entry if the client can't render a QR code."
    )


class MFAVerifySerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=6)


class MFAStatusResponseSerializer(serializers.Serializer):
    status = serializers.CharField()


class MFALoginChallengeSerializer(serializers.Serializer):
    mfa_required = serializers.BooleanField(default=True)
    mfa_token = serializers.CharField()


class MFALoginVerifySerializer(serializers.Serializer):
    mfa_token = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["first_name", "last_name", "avatar_url", "locale", "timezone"]


class MeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ["id", "email", "is_active", "created_at", "profile"]
        read_only_fields = ["id", "email", "is_active", "created_at"]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)
        if profile_data:
            for field, value in profile_data.items():
                setattr(instance.profile, field, value)
            instance.profile.save()
        return instance
