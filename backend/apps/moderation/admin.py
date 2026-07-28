from django.contrib import admin

from .models import InstructorApplication


@admin.register(InstructorApplication)
class InstructorApplicationAdmin(admin.ModelAdmin):
    list_display = ["user", "status", "applied_at", "approved_at", "approved_by"]
    list_filter = ["status"]
    search_fields = ["user__email"]
