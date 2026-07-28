from django.contrib import admin

from .models import Message, Thread, ThreadParticipant


class ThreadParticipantInline(admin.TabularInline):
    model = ThreadParticipant
    extra = 0


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ["id", "thread_type", "subject", "created_by", "created_at"]
    list_filter = ["thread_type"]
    inlines = [ThreadParticipantInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["thread", "sender", "created_at"]
    search_fields = ["body", "sender__email"]
