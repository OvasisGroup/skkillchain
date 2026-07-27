from django.contrib import admin

from .models import Category, Course, CourseLearningObjective, CoursePrerequisite, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


class PrerequisiteInline(admin.TabularInline):
    model = CoursePrerequisite
    extra = 1


class LearningObjectiveInline(admin.TabularInline):
    model = CourseLearningObjective
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "owner",
        "status",
        "difficulty",
        "price_amount",
        "currency",
        "published_at",
    ]
    list_filter = ["status", "difficulty", "language"]
    search_fields = ["title", "owner__email"]
    readonly_fields = ["id", "slug", "created_at", "updated_at", "published_at"]
    autocomplete_fields = ["owner"]
    inlines = [PrerequisiteInline, LearningObjectiveInline]
