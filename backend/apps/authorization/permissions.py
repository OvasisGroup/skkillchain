from django.core.cache import cache
from rest_framework.permissions import BasePermission

from .models import UserRole

_CACHE_TTL_SECONDS = 60


def user_has_permission(user, codename, context_type="platform", context_id=None):
    """codename is "<resource>.<action>", e.g. "courses.approve"."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True

    cache_key = f"perm:{user.id}:{context_type}:{context_id}"
    codenames = cache.get(cache_key)
    if codenames is None:
        roles = UserRole.objects.filter(
            user=user, context_type=context_type, context_id=context_id
        ).prefetch_related("role__permissions")
        codenames = set()
        for user_role in roles:
            for permission in user_role.role.permissions.all():
                codenames.add(permission.codename)
        cache.set(cache_key, codenames, timeout=_CACHE_TTL_SECONDS)

    return codename in codenames


class HasPermission(BasePermission):
    """
    Usage:
        class ApproveCourseView(APIView):
            permission_classes = [HasPermission]
            required_permission = "courses.approve"
            # optional: permission_context_type = "organization"
    """

    def has_permission(self, request, view):
        codename = getattr(view, "required_permission", None)
        if codename is None:
            raise AssertionError(f"{view.__class__.__name__} must define required_permission")
        context_type = getattr(view, "permission_context_type", "platform")
        return user_has_permission(request.user, codename, context_type=context_type)
