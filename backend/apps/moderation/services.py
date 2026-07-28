from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.authorization.models import Role, UserRole

from .models import InstructorApplication


def apply_as_instructor(user) -> InstructorApplication:
    application, _created = InstructorApplication.objects.get_or_create(user=user)
    return application


def approve_instructor_application(user_id, approved_by) -> InstructorApplication:
    application = get_object_or_404(InstructorApplication, user_id=user_id)
    application.status = InstructorApplication.STATUS_APPROVED
    application.approved_at = timezone.now()
    application.approved_by = approved_by
    application.save(update_fields=["status", "approved_at", "approved_by"])

    role = get_object_or_404(Role, code="instructor")
    UserRole.objects.get_or_create(
        user_id=user_id, role=role, context_type=Role.SCOPE_PLATFORM, context_id=None
    )
    return application
