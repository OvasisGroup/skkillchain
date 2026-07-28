from django.contrib import admin

from .models import ConferencingAccount, LiveSession, LiveSessionRecording, LiveSessionRegistration


@admin.register(ConferencingAccount)
class ConferencingAccountAdmin(admin.ModelAdmin):
    list_display = ["user", "provider", "connected_at", "revoked_at"]
    list_filter = ["provider"]
    search_fields = ["user__email"]
    # Encrypted token fields are deliberately excluded from readonly_fields
    # display too — never surface even the ciphertext in the admin UI.
    readonly_fields = ["id", "connected_at"]
    exclude = ["access_token_encrypted", "refresh_token_encrypted"]


class LiveSessionRegistrationInline(admin.TabularInline):
    model = LiveSessionRegistration
    extra = 0
    readonly_fields = ["registered_at", "joined_at", "left_at"]


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "host", "provider", "status", "scheduled_start_at"]
    list_filter = ["status", "provider"]
    search_fields = ["title", "host__email", "course__title"]
    readonly_fields = ["id", "external_meeting_id", "join_url", "host_join_url"]
    inlines = [LiveSessionRegistrationInline]


@admin.register(LiveSessionRecording)
class LiveSessionRecordingAdmin(admin.ModelAdmin):
    list_display = ["live_session", "duration_seconds", "available_at"]
    search_fields = ["live_session__title"]
