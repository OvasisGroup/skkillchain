from django.contrib import admin

from .models import CourseDiscussionPost, Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["course", "user", "rating", "is_verified_purchase", "created_at"]
    list_filter = ["rating", "is_verified_purchase"]
    search_fields = ["course__title", "user__email"]


@admin.register(CourseDiscussionPost)
class CourseDiscussionPostAdmin(admin.ModelAdmin):
    list_display = ["course", "user", "created_at"]
    search_fields = ["course__title", "user__email", "body"]
