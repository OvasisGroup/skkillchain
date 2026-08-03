# Replaces Course's many-to-many `categories` (through CourseCategory) with
# a single `category` FK — a course belongs to exactly one category. The
# RunPython step backfills `category` from each course's existing
# CourseCategory rows (first one, alphabetically by slug) before that
# M2M/through table is dropped, so no existing category assignment is lost.

import django.db.models.deletion
from django.db import migrations, models


def backfill_category(apps, schema_editor):
    Course = apps.get_model("catalog", "Course")
    CourseCategory = apps.get_model("catalog", "CourseCategory")

    course_ids_with_category = CourseCategory.objects.values_list(
        "course_id", flat=True
    ).distinct()
    for course_id in course_ids_with_category:
        first_link = (
            CourseCategory.objects.filter(course_id=course_id)
            .order_by("category__slug")
            .first()
        )
        Course.objects.filter(pk=course_id).update(category_id=first_link.category_id)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_course_cover_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="courses_by_category_tmp",
                to="catalog.category",
            ),
        ),
        migrations.RunPython(backfill_category, noop),
        migrations.RemoveField(
            model_name="course",
            name="categories",
        ),
        migrations.DeleteModel(
            name="CourseCategory",
        ),
        migrations.AlterField(
            model_name="course",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="courses",
                to="catalog.category",
            ),
        ),
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(blank=True, max_length=170, unique=True),
        ),
        migrations.AlterField(
            model_name="tag",
            name="slug",
            field=models.SlugField(blank=True, max_length=120, unique=True),
        ),
    ]
