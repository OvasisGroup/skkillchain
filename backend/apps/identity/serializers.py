from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.authorization.models import UserRole

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
    # avatar is read/displayed here, but only ever *written* through the
    # dedicated POST /auth/me/avatar/ (AvatarUploadView) — a file can't
    # travel through this field via a plain JSON PATCH, and multipart data
    # can't populate a serializer nested this deeply, so upload gets its
    # own single-purpose endpoint instead.
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


class AvatarUploadSerializer(serializers.Serializer):
    avatar = serializers.ImageField()


class MeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "is_active", "created_at", "profile", "roles"]
        read_only_fields = ["id", "is_active", "created_at", "roles"]
        # Uniqueness is enforced in validate_email() below instead of DRF's
        # auto-generated UniqueValidator, so a duplicate email gets the same
        # message (and normalize_email() casing) as RegisterSerializer rather
        # than DRF's generic "user with this email already exists.".
        extra_kwargs: dict[str, dict[str, Any]] = {"email": {"validators": []}}

    def validate_email(self, value):
        value = User.objects.normalize_email(value)
        qs = User.objects.filter(email=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def get_roles(self, obj) -> list[str]:
        codes = set(
            UserRole.objects.filter(user=obj).values_list("role__code", flat=True).distinct()
        )
        # user_has_permission() (apps/authorization/permissions.py) already lets
        # superusers bypass RBAC entirely; reflect that here too, or a superuser
        # with no UserRole rows reports no roles and the frontend routes them to
        # the student dashboard instead of admin.
        if obj.is_superuser:
            codes.add("super_administrator")
        return list(codes)

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)
        email = validated_data.pop("email", None)
        if email is not None and email != instance.email:
            instance.email = email
            instance.save(update_fields=["email"])
        if profile_data:
            for field, value in profile_data.items():
                setattr(instance.profile, field, value)
            instance.profile.save()
        return instance
