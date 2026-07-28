# Seeds the "instructors.approve" permission (used by
# AdminInstructorListView / AdminInstructorApproveView) and attaches it to
# the roles covering account-level moderation: moderator, administrator,
# super_administrator.

from django.db import migrations

ROLE_CODES = ["moderator", "administrator", "super_administrator"]


def seed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Role = apps.get_model("authorization", "Role")
    RolePermission = apps.get_model("authorization", "RolePermission")

    permission, _ = Permission.objects.get_or_create(resource="instructors", action="approve")
    for code in ROLE_CODES:
        role = Role.objects.filter(code=code).first()
        if role is not None:
            RolePermission.objects.get_or_create(role=role, permission=permission)


def unseed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Permission.objects.filter(resource="instructors", action="approve").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("moderation", "0001_initial"),
        ("authorization", "0002_seed_platform_roles"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
