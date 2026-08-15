# Seeds the "courses.manage" permission (used by AdminCourseListView /
# AdminCourseDetailView / AdminCourseNotifyView — full course CRUD across
# every owner/status, distinct from the review-only "courses.approve") and
# attaches it to administrator/super_administrator only. content_reviewer
# is deliberately excluded — that role's PRD scope is review/approve, not
# full editing or creating courses on an instructor's behalf.

from django.db import migrations

ROLE_CODES = ["administrator", "super_administrator"]


def seed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Role = apps.get_model("authorization", "Role")
    RolePermission = apps.get_model("authorization", "RolePermission")

    permission, _ = Permission.objects.get_or_create(resource="courses", action="manage")
    for code in ROLE_CODES:
        role = Role.objects.filter(code=code).first()
        if role is not None:
            RolePermission.objects.get_or_create(role=role, permission=permission)


def unseed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Permission.objects.filter(resource="courses", action="manage").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0006_course_search_trigram_index"),
        ("authorization", "0002_seed_platform_roles"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
