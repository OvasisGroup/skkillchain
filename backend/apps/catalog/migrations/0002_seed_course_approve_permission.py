# Seeds the "courses.approve" permission (used by CourseApproveView /
# CourseRejectView / CoursesPendingReviewView) and attaches it to the roles
# whose PRD description covers content review: content_reviewer,
# administrator, super_administrator.

from django.db import migrations

ROLE_CODES = ["content_reviewer", "administrator", "super_administrator"]


def seed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Role = apps.get_model("authorization", "Role")
    RolePermission = apps.get_model("authorization", "RolePermission")

    permission, _ = Permission.objects.get_or_create(resource="courses", action="approve")
    for code in ROLE_CODES:
        role = Role.objects.filter(code=code).first()
        if role is not None:
            RolePermission.objects.get_or_create(role=role, permission=permission)


def unseed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Permission.objects.filter(resource="courses", action="approve").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
        ("authorization", "0002_seed_platform_roles"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
