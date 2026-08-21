from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.authorization.models import Role, UserRole
from apps.authorization.permissions import HasPermission

from .admin_serializers import (
    AdminAvatarUploadSerializer,
    AdminProfileSerializer,
    AdminUserSerializer,
    AdminUserStatusUpdateSerializer,
)
from .models import User

_ADMIN_PROFILE_EXAMPLE = {
    "first_name": "",
    "last_name": "",
    "bio": "",
    "avatar": "",
    "locale": "en",
    "timezone": "UTC",
    "linkedin_url": "",
    "twitter_url": "",
    "github_url": "",
    "youtube_url": "",
    "website_url": "",
}

_ADMIN_USER_EXAMPLE = {
    "id": "b6a5b6c0-9b1e-4c9a-9b7a-1f2e3d4c5b6a",
    "email": "student@example.com",
    "is_active": True,
    "created_at": "2026-01-15T09:00:00Z",
    "profile": _ADMIN_PROFILE_EXAMPLE,
}


@extend_schema(
    tags=["Admin"],
    parameters=[
        OpenApiParameter(
            "email",
            str,
            description="Case-insensitive substring filter matched against email, first name, "
            "or last name — e.g. 'mary' matches mary.usaji@gmail.com and matches a profile "
            "first_name of 'Mary' equally, so an admin can search by either.",
        ),
        OpenApiParameter(
            "role",
            str,
            description="Filter to users holding this role code, e.g. 'instructor'. For "
            "'instructor' specifically, also includes users who own at least one course but "
            "were never granted the role directly (e.g. a course created for them by an admin) "
            "— so this always reflects everyone who should show up as an instructor, not just "
            "role assignments.",
        ),
    ],
    description="Lists platform users, optionally filtered by an email/name substring and/or role.",
    examples=[OpenApiExample("User", value=_ADMIN_USER_EXAMPLE, response_only=True)],
)
class AdminUserListView(generics.ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [HasPermission]
    required_permission = "users.manage"

    def get_queryset(self):
        queryset = User.objects.select_related("profile")
        search = self.request.query_params.get("email")
        if search:
            # Named "email" for backwards compatibility with existing callers,
            # but matched against the profile's name too — an admin naturally
            # searches by the name shown in the UI, not the email address
            # (e.g. a "Mary Usaji" search shouldn't come up empty just
            # because her email is mary.usaji@gmail.com).
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(profile__first_name__icontains=search)
                | Q(profile__last_name__icontains=search)
            ).distinct()
        role = self.request.query_params.get("role")
        if role == "instructor":
            # Role membership alone misses a user who owns a course but was
            # never granted the role (e.g. an admin created a draft course
            # on their behalf via AdminCourseCreateInput.owner_id before
            # onboarding them) — union both so the admin instructor list
            # never silently hides someone who clearly needs managing.
            queryset = queryset.filter(
                Q(user_roles__role__code=role) | Q(owned_courses__isnull=False)
            ).distinct()
        elif role:
            queryset = queryset.filter(user_roles__role__code=role).distinct()
        return queryset


@extend_schema(
    tags=["Admin"],
    request=AdminUserStatusUpdateSerializer,
    responses={200: AdminUserSerializer},
    description="Suspends or reinstates a user account by toggling is_active.",
    examples=[
        OpenApiExample("Suspend", value={"is_active": False}, request_only=True),
        OpenApiExample(
            "Suspended",
            value={**_ADMIN_USER_EXAMPLE, "is_active": False},
            response_only=True,
        ),
    ],
)
class AdminUserStatusUpdateView(APIView):
    permission_classes = [HasPermission]
    required_permission = "users.manage"
    throttle_scope = "admin-write"

    def patch(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        serializer = AdminUserStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_active = serializer.validated_data["is_active"]

        user.is_active = is_active
        user.save(update_fields=["is_active"])
        record_event(
            actor=request.user,
            action="user.reinstate" if is_active else "user.suspend",
            entity_type="User",
            entity_id=user.id,
            request=request,
        )
        return Response(AdminUserSerializer(user).data)


@extend_schema(
    tags=["Admin"],
    request=AdminProfileSerializer,
    responses={200: AdminProfileSerializer},
    description="Views or updates a user's profile (name, bio, locale, timezone, social "
    "links) on their behalf — for maintaining instructor details from the admin dashboard. "
    "To change the avatar image itself, use POST .../avatar/ instead — a file can't travel "
    "through this JSON endpoint.",
    examples=[OpenApiExample("Profile", value=_ADMIN_PROFILE_EXAMPLE, response_only=True)],
)
class AdminUserProfileView(APIView):
    permission_classes = [HasPermission]
    required_permission = "users.manage"
    throttle_scope = "admin-write"

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        return Response(AdminProfileSerializer(user.profile).data)

    def patch(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        serializer = AdminProfileSerializer(user.profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_event(
            actor=request.user,
            action="user.profile_update",
            entity_type="Profile",
            entity_id=user.id,
            request=request,
        )
        return Response(serializer.data)


@extend_schema(
    tags=["Admin"],
    request=AdminAvatarUploadSerializer,
    responses={200: AdminProfileSerializer},
    description="Uploads (or replaces) a user's avatar image on their behalf. Send as "
    "multipart/form-data with a single 'avatar' file field.",
)
class AdminUserAvatarUploadView(APIView):
    permission_classes = [HasPermission]
    required_permission = "users.manage"
    throttle_scope = "admin-write"

    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        serializer = AdminAvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile = user.profile
        profile.avatar = serializer.validated_data["avatar"]
        profile.save(update_fields=["avatar"])
        record_event(
            actor=request.user,
            action="user.avatar_update",
            entity_type="Profile",
            entity_id=user.id,
            request=request,
        )
        return Response(AdminProfileSerializer(profile).data)


@extend_schema(
    tags=["Admin"],
    responses={204: None},
    description="Revokes a platform-scoped role from a user — e.g. removing someone from the "
    "admin instructors list. Only the role grant is removed: courses they already own aren't "
    "touched (Course.owner is protected against deletion) and they keep editing them, since "
    "curriculum authoring is scoped by ownership, not role. An admin can no longer pick this "
    "user as the owner of a *new* course via AdminCourseWriteSerializer's owner_id until the "
    "role is granted again. 404s if the user never held this role.",
)
class AdminUserRoleRevokeView(APIView):
    permission_classes = [HasPermission]
    required_permission = "users.manage"
    throttle_scope = "admin-write"

    def delete(self, request, user_id, role_code):
        user = get_object_or_404(User, pk=user_id)
        role = get_object_or_404(Role, code=role_code)
        deleted, _ = UserRole.objects.filter(
            user=user, role=role, context_type=Role.SCOPE_PLATFORM, context_id=None
        ).delete()
        if not deleted:
            raise NotFound(f"{user.email} does not hold the '{role_code}' role.")

        record_event(
            actor=request.user,
            action="user.role_revoke",
            entity_type="UserRole",
            entity_id=user.id,
            request=request,
            payload={"role": role_code},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
