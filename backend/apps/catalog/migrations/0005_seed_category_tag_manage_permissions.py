# Seeds the "categories.manage" and "tags.manage" permissions (used by
# CategoryListCreateView/CategoryDetailView and TagDetailView — tag *creation*
# is open to any authenticated user, see TagListCreateView.post) and attaches
# them to administrator/super_administrator, the roles responsible for
# curating the platform's taxonomy.

from django.db import migrations

ROLE_CODES = ["administrator", "super_administrator"]
RESOURCE_ACTIONS = [("categories", "manage"), ("tags", "manage")]


def seed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Role = apps.get_model("authorization", "Role")
    RolePermission = apps.get_model("authorization", "RolePermission")

    roles = list(Role.objects.filter(code__in=ROLE_CODES))
    for resource, action in RESOURCE_ACTIONS:
        permission, _ = Permission.objects.get_or_create(resource=resource, action=action)
        for role in roles:
            RolePermission.objects.get_or_create(role=role, permission=permission)


def unseed(apps, schema_editor):
    Permission = apps.get_model("authorization", "Permission")
    Permission.objects.filter(
        resource__in=[resource for resource, _ in RESOURCE_ACTIONS],
        action="manage",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_remove_course_categories_course_category_and_more"),
        ("authorization", "0002_seed_platform_roles"),
    ]

    operations = [migrations.RunPython(seed, unseed)]
