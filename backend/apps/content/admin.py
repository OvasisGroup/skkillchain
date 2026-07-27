from django.contrib import admin

from .models import Lesson, Section


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "sort_order"]
    search_fields = ["title", "course__title"]
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "section", "lesson_type", "sort_order", "is_preview"]
    list_filter = ["lesson_type", "is_preview"]
    search_fields = ["title"]
