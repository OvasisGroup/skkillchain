from django.contrib import admin

from .models import BlogPost, BlogTag


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "status", "published_at", "created_at"]
    list_filter = ["status", "tags"]
    search_fields = ["title", "summary", "author__email"]
    readonly_fields = ["id", "slug", "published_at", "created_at", "updated_at"]
    filter_horizontal = ["tags"]


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    readonly_fields = ["id", "slug"]
