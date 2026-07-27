import uuid

from django.conf import settings
from django.db import models


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource = models.CharField(max_length=100)
    action = models.CharField(max_length=100)

    class Meta:
        db_table = "permissions"
        constraints = [
            models.UniqueConstraint(
                fields=["resource", "action"], name="uniq_permission_resource_action"
            )
        ]

    def __str__(self):
        return self.codename

    @property
    def codename(self):
        return f"{self.resource}.{self.action}"


class Role(models.Model):
    SCOPE_PLATFORM = "platform"
    SCOPE_ORGANIZATION = "organization"
    SCOPE_CHOICES = [(SCOPE_PLATFORM, "Platform"), (SCOPE_ORGANIZATION, "Organization")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default=SCOPE_PLATFORM)
    permissions: models.ManyToManyField = models.ManyToManyField(
        Permission, through="RolePermission", related_name="roles"
    )

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = "role_permissions"
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="uniq_role_permission")
        ]

    def __str__(self):
        return f"{self.role} -> {self.permission}"


class UserRole(models.Model):
    """context_type/context_id let the same role mean something different per
    scope — e.g. "org_admin" for organization <context_id> vs. platform-wide."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    context_type = models.CharField(max_length=50, default=Role.SCOPE_PLATFORM)
    context_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "user_roles"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role", "context_type", "context_id"],
                name="uniq_user_role_context",
            )
        ]

    def __str__(self):
        return f"{self.user} as {self.role} ({self.context_type})"
