# Seeds "reports.view_revenue" (financial data — finance_officer/
# administrator) and "reports.view" (the rest of the analytics/admin
# report endpoints — content_reviewer/administrator), used by
# apps.analytics.views.

from django.db import migrations

REVENUE_ROLE_CODES = ["finance_officer", "administrator", "super_administrator"]
GENERAL_ROLE_CODES = ["content_reviewer", "administrator", "super_administrator"]


def seed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Role = apps.get_model("authorization", "Role")
    RolePermission = apps.get_model("authorization", "RolePermission")

    revenue_permission, _ = Permission.objects.get_or_create(resource="reports", action="view_revenue")
    for code in REVENUE_ROLE_CODES:
        role = Role.objects.filter(code=code).first()
        if role is not None:
            RolePermission.objects.get_or_create(role=role, permission=revenue_permission)

    general_permission, _ = Permission.objects.get_or_create(resource="reports", action="view")
    for code in GENERAL_ROLE_CODES:
        role = Role.objects.filter(code=code).first()
        if role is not None:
            RolePermission.objects.get_or_create(role=role, permission=general_permission)


def unseed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Permission.objects.filter(resource="reports", action__in=["view_revenue", "view"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0001_initial"),
        ("authorization", "0002_seed_platform_roles"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
