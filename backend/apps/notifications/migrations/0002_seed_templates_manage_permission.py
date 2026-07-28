# Seeds the "templates.manage" permission (used by the admin
# email-template/notification-template views) and attaches it to
# content_reviewer/administrator.

from django.db import migrations

ROLE_CODES = ["content_reviewer", "administrator", "super_administrator"]


def seed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Role = apps.get_model("authorization", "Role")
    RolePermission = apps.get_model("authorization", "RolePermission")

    permission, _ = Permission.objects.get_or_create(resource="templates", action="manage")
    for code in ROLE_CODES:
        role = Role.objects.filter(code=code).first()
        if role is not None:
            RolePermission.objects.get_or_create(role=role, permission=permission)


def unseed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Permission.objects.filter(resource="templates", action="manage").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0001_initial"),
        ("authorization", "0002_seed_platform_roles"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
