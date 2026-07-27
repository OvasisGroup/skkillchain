# Seeds the 11 user roles from docs/00-product/01-prd.md §4 (User Segments).
# Permissions are attached incrementally as each domain app is built in later
# milestones — this migration only establishes the role identities.

from django.db import migrations

ROLES = [
    ("guest", "Guest", "platform"),
    ("student", "Student", "platform"),
    ("instructor", "Instructor", "platform"),
    ("organization", "Organization", "organization"),
    ("affiliate", "Affiliate", "platform"),
    ("moderator", "Moderator", "platform"),
    ("support_agent", "Support Agent", "platform"),
    ("finance_officer", "Finance Officer", "platform"),
    ("content_reviewer", "Content Reviewer", "platform"),
    ("administrator", "Administrator", "platform"),
    ("super_administrator", "Super Administrator", "platform"),
]


def seed_roles(apps, schema_editor):
    Role = apps.get_model("authorization", "Role")
    for code, name, scope in ROLES:
        Role.objects.update_or_create(code=code, defaults={"name": name, "scope": scope})


def remove_roles(apps, schema_editor):
    Role = apps.get_model("authorization", "Role")
    Role.objects.filter(code__in=[code for code, _, _ in ROLES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("authorization", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles, remove_roles),
    ]
