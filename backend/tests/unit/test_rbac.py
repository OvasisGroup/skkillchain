import pytest
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.authorization.models import Permission, Role, UserRole
from apps.authorization.permissions import HasPermission, user_has_permission

pytestmark = pytest.mark.django_db


class _ProtectedView(APIView):
    permission_classes = [HasPermission]
    required_permission = "courses.approve"

    def get(self, request):
        return Response({"ok": True})


def _grant(user, resource, action, code):
    permission = Permission.objects.create(resource=resource, action=action)
    role = Role.objects.create(code=code, name=code)
    role.permissions.add(permission)
    UserRole.objects.create(user=user, role=role)
    return role, permission


class TestUserHasPermission:
    def test_superuser_always_allowed(self, django_user_model):
        user = django_user_model.objects.create_superuser(email="root@example.com", password="x")

        assert user_has_permission(user, "anything.at-all") is True

    def test_anonymous_denied(self):
        assert user_has_permission(None, "courses.approve") is False

    def test_denied_without_role(self, django_user_model):
        user = django_user_model.objects.create_user(email="plain@example.com", password="x")

        assert user_has_permission(user, "courses.approve") is False

    def test_granted_via_role(self, django_user_model):
        user = django_user_model.objects.create_user(email="reviewer@example.com", password="x")
        _grant(user, "courses", "approve", "reviewer")

        assert user_has_permission(user, "courses.approve") is True
        assert user_has_permission(user, "courses.reject") is False

    def test_context_scoped_role_does_not_leak_to_other_context(self, django_user_model):
        import uuid

        user = django_user_model.objects.create_user(email="org-admin@example.com", password="x")
        permission = Permission.objects.create(resource="org", action="manage")
        role = Role.objects.create(code="org_admin", name="Org Admin", scope="organization")
        role.permissions.add(permission)
        org_a = uuid.uuid4()
        org_b = uuid.uuid4()
        UserRole.objects.create(user=user, role=role, context_type="organization", context_id=org_a)

        assert (
            user_has_permission(user, "org.manage", context_type="organization", context_id=org_a)
            is True
        )
        assert (
            user_has_permission(user, "org.manage", context_type="organization", context_id=org_b)
            is False
        )


class TestHasPermissionView:
    def test_forbidden_without_role_is_audit_logged(self, django_user_model):
        user = django_user_model.objects.create_user(email="student@example.com", password="x")
        request = APIRequestFactory().get("/protected/")
        force_authenticate(request, user=user)

        response = _ProtectedView.as_view()(request)

        assert response.status_code == 403
        assert AuditLog.objects.filter(action="access.denied", actor=user).exists()

    def test_allowed_with_role(self, django_user_model):
        user = django_user_model.objects.create_user(email="reviewer2@example.com", password="x")
        _grant(user, "courses", "approve", "reviewer2")
        request = APIRequestFactory().get("/protected/")
        force_authenticate(request, user=user)

        response = _ProtectedView.as_view()(request)

        assert response.status_code == 200

    def test_anonymous_gets_401_not_500(self):
        request = APIRequestFactory().get("/protected/")

        response = _ProtectedView.as_view()(request)

        assert response.status_code == 401
