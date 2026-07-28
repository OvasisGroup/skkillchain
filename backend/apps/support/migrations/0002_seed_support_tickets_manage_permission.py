# Seeds the "support_tickets.manage" permission (used by the admin
# support-ticket views — the admin half explicitly deferred from M7) and
# attaches it to support_agent/administrator.

from django.db import migrations

ROLE_CODES = ["support_agent", "administrator", "super_administrator"]


def seed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Role = apps.get_model("authorization", "Role")
    RolePermission = apps.get_model("authorization", "RolePermission")

    permission, _ = Permission.objects.get_or_create(resource="support_tickets", action="manage")
    for code in ROLE_CODES:
        role = Role.objects.filter(code=code).first()
        if role is not None:
            RolePermission.objects.get_or_create(role=role, permission=permission)


def unseed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Permission.objects.filter(resource="support_tickets", action="manage").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("support", "0001_initial"),
        ("authorization", "0002_seed_platform_roles"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
