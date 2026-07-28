from django.contrib import admin

from .models import SupportTicket, SupportTicketMessage


class SupportTicketMessageInline(admin.TabularInline):
    model = SupportTicketMessage
    extra = 0


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ["subject", "requester", "assignee", "category", "priority", "status", "created_at"]
    list_filter = ["category", "priority", "status"]
    search_fields = ["subject", "requester__email"]
    inlines = [SupportTicketMessageInline]
