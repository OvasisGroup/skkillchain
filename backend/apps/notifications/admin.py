from django.contrib import admin

from .models import EmailTemplate, Notification, NotificationTemplate


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ["code", "channel", "locale", "is_active"]
    list_filter = ["channel", "is_active"]
    search_fields = ["code"]


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ["code", "locale", "subject", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "subject"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "type", "channel", "read_at", "sent_at", "created_at"]
    list_filter = ["type", "channel"]
    search_fields = ["user__email", "title"]
