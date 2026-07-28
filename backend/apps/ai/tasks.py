import logging

from celery import shared_task
from django.utils import timezone

from . import services
from .anthropic_client import AIProviderError
from .models import AiGenerationJob

logger = logging.getLogger(__name__)


@shared_task(name="ai.dispatch_generation_job", time_limit=120)
def dispatch_generation_job(job_id: str) -> None:
    try:
        job = AiGenerationJob.objects.get(id=job_id)
    except AiGenerationJob.DoesNotExist:
        return

    job.status = AiGenerationJob.STATUS_RUNNING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    try:
        services.run_generation_job(job)
    except Exception as exc:
        job.status = AiGenerationJob.STATUS_FAILED
        job.error_message = str(exc)
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at"])
        if not isinstance(exc, AIProviderError):
            logger.exception("ai.dispatch_generation_job: job %s failed unexpectedly", job_id)
        return

    job.status = AiGenerationJob.STATUS_COMPLETED
    job.completed_at = timezone.now()
    job.save(update_fields=["status", "completed_at"])
