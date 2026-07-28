from django.contrib import admin

from .models import AiChatMessage, AiChatSession, AiGeneratedContent, AiGenerationJob, Flashcard


class AiChatMessageInline(admin.TabularInline):
    model = AiChatMessage
    extra = 0


@admin.register(AiChatSession)
class AiChatSessionAdmin(admin.ModelAdmin):
    list_display = ["user", "course", "context_type", "started_at", "ended_at"]
    inlines = [AiChatMessageInline]


@admin.register(AiGenerationJob)
class AiGenerationJobAdmin(admin.ModelAdmin):
    list_display = ["job_type", "source_type", "source_id", "status", "requested_by"]
    list_filter = ["job_type", "status"]


@admin.register(AiGeneratedContent)
class AiGeneratedContentAdmin(admin.ModelAdmin):
    list_display = ["content_type", "source_type", "source_id", "model_used", "created_at"]
    list_filter = ["content_type"]


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ["course", "lesson", "generated_by", "created_at"]
