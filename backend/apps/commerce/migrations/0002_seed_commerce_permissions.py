# Seeds "coupons.manage" and "promotions.manage" (used by
# AdminCouponListCreateView / AdminPromotionListCreateView /
# AdminPromotionUpdateView) and attaches them to the roles whose PRD
# description covers platform-wide financial/promotional administration:
# finance_officer, administrator, super_administrator. Same pattern as
# apps/catalog/migrations/0002_seed_course_approve_permission.py.

from django.db import migrations

ROLE_CODES = ["finance_officer", "administrator", "super_administrator"]
PERMISSIONS = [("coupons", "manage"), ("promotions", "manage")]


def seed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Role = apps.get_model("authorization", "Role")
    RolePermission = apps.get_model("authorization", "RolePermission")

    roles = [role for role in Role.objects.filter(code__in=ROLE_CODES)]
    for resource, action in PERMISSIONS:
        permission, _ = Permission.objects.get_or_create(resource=resource, action=action)
        for role in roles:
            RolePermission.objects.get_or_create(role=role, permission=permission)


def unseed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    for resource, action in PERMISSIONS:
        Permission.objects.filter(resource=resource, action=action).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("commerce", "0001_initial"),
        ("authorization", "0002_seed_platform_roles"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
