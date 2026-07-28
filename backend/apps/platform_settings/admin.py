from django.contrib import admin

from .models import Setting


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ["scope_type", "scope_id", "key", "updated_at"]
    search_fields = ["key"]
