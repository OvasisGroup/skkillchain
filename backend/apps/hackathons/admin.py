from django.contrib import admin

from .models import Hackathon, HackathonRegistration, HackathonSubmission, HackathonWinner


class HackathonRegistrationInline(admin.TabularInline):
    model = HackathonRegistration
    extra = 0
    readonly_fields = ["id", "registered_at"]


@admin.register(Hackathon)
class HackathonAdmin(admin.ModelAdmin):
    list_display = ["title", "host_type", "status", "starts_at", "ends_at", "organizer"]
    list_filter = ["status", "host_type"]
    search_fields = ["title", "organizer__email", "partner_name"]
    readonly_fields = ["id", "slug", "published_at"]
    inlines = [HackathonRegistrationInline]


@admin.register(HackathonRegistration)
class HackathonRegistrationAdmin(admin.ModelAdmin):
    list_display = ["participant", "hackathon", "status", "registered_at"]
    list_filter = ["status"]
    search_fields = ["participant__email", "hackathon__title", "team_name"]
    readonly_fields = ["id", "registered_at"]


@admin.register(HackathonSubmission)
class HackathonSubmissionAdmin(admin.ModelAdmin):
    list_display = ["title", "registration", "submitted_at"]
    search_fields = ["title", "registration__participant__email"]
    readonly_fields = ["id", "submitted_at"]


@admin.register(HackathonWinner)
class HackathonWinnerAdmin(admin.ModelAdmin):
    list_display = ["hackathon", "placement", "submission", "announced_at"]
    list_filter = ["placement"]
    readonly_fields = ["id", "announced_at"]
