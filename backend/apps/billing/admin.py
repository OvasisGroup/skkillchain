from django.contrib import admin

from .models import Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "billing_interval", "price_amount", "currency", "is_active"]
    search_fields = ["code", "name"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["subscriber_type", "subscriber_id", "plan", "status", "started_at", "renews_at"]
    list_filter = ["status", "subscriber_type"]
    readonly_fields = ["id", "started_at"]
