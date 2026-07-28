from django.contrib import admin

from .models import (
    Bookmark,
    Certificate,
    Enrollment,
    LessonNote,
    ProgressTracking,
    RecentlyViewed,
    Wishlist,
    WishlistItem,
)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "status", "source", "enrolled_at", "completed_at"]
    list_filter = ["status", "source"]
    search_fields = ["student__email", "course__title"]
    readonly_fields = ["id", "enrolled_at", "completed_at"]


@admin.register(ProgressTracking)
class ProgressTrackingAdmin(admin.ModelAdmin):
    list_display = ["enrollment", "lesson", "percent_complete", "last_viewed_at"]
    search_fields = ["enrollment__student__email", "lesson__title"]


@admin.register(LessonNote)
class LessonNoteAdmin(admin.ModelAdmin):
    list_display = ["student", "lesson", "timestamp_seconds", "created_at"]
    search_fields = ["student__email", "lesson__title"]


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ["student", "lesson", "timestamp_seconds", "label"]
    search_fields = ["student__email", "lesson__title"]


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at"]
    search_fields = ["user__email"]
    inlines = [WishlistItemInline]


@admin.register(RecentlyViewed)
class RecentlyViewedAdmin(admin.ModelAdmin):
    list_display = ["user", "course", "viewed_at"]
    search_fields = ["user__email", "course__title"]


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ["certificate_uid", "enrollment", "issued_at"]
    search_fields = ["certificate_uid", "enrollment__student__email"]
    readonly_fields = ["id", "certificate_uid", "qr_payload", "issued_at"]
