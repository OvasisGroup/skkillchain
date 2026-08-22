# Seeds the "cms.manage" permission (used by AdminBlogPostListView /
# AdminBlogPostDetailView / AdminBlogPostUnpublishView etc.) and attaches it
# to the roles whose PRD description covers platform-wide content oversight:
# moderator, administrator, super_administrator — same seed-migration
# pattern as "hackathons.manage" (apps.hackathons 0002). Any authenticated
# user can still write and publish their own blog posts — this permission
# is only for acting on a post you don't own.

from django.db import migrations

ROLE_CODES = ["moderator", "administrator", "super_administrator"]


def seed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Role = apps.get_model("authorization", "Role")
    RolePermission = apps.get_model("authorization", "RolePermission")

    permission, _ = Permission.objects.get_or_create(resource="cms", action="manage")
    for code in ROLE_CODES:
        role = Role.objects.filter(code=code).first()
        if role is not None:
            RolePermission.objects.get_or_create(role=role, permission=permission)


def unseed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Permission.objects.filter(resource="cms", action="manage").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0001_initial"),
        ("authorization", "0002_seed_platform_roles"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
