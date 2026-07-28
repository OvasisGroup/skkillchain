# Seeds the "privacy.manage" permission (used by AdminErasureRequestListView /
# AdminLegalHoldCreateView / AdminLegalHoldReleaseView) and attaches it to the
# roles with platform-wide compliance authority: administrator,
# super_administrator.

from django.db import migrations

ROLE_CODES = ["administrator", "super_administrator"]


def seed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Role = apps.get_model("authorization", "Role")
    RolePermission = apps.get_model("authorization", "RolePermission")

    permission, _ = Permission.objects.get_or_create(resource="privacy", action="manage")
    for code in ROLE_CODES:
        role = Role.objects.filter(code=code).first()
        if role is not None:
            RolePermission.objects.get_or_create(role=role, permission=permission)


def unseed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Permission.objects.filter(resource="privacy", action="manage").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("privacy", "0001_initial"),
        ("authorization", "0002_seed_platform_roles"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
