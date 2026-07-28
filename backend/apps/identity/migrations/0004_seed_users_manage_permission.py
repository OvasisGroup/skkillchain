# Seeds the "users.manage" permission (used by AdminUserListView /
# AdminUserStatusUpdateView) and attaches it to administrator/
# super_administrator.

from django.db import migrations

ROLE_CODES = ["administrator", "super_administrator"]


def seed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Role = apps.get_model("authorization", "Role")
    RolePermission = apps.get_model("authorization", "RolePermission")

    permission, _ = Permission.objects.get_or_create(resource="users", action="manage")
    for code in ROLE_CODES:
        role = Role.objects.filter(code=code).first()
        if role is not None:
            RolePermission.objects.get_or_create(role=role, permission=permission)


def unseed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Permission.objects.filter(resource="users", action="manage").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("identity", "0003_mfafactor_oauthidentity"),
        ("authorization", "0002_seed_platform_roles"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
