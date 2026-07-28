from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.learning.models import Enrollment

from .models import CourseDiscussionPost, Review


def _has_completed_enrollment(user, course_id) -> bool:
    return Enrollment.objects.filter(
        course_id=course_id, student=user, status=Enrollment.STATUS_COMPLETED
    ).exists()


def _has_any_enrollment(user, course_id) -> bool:
    return Enrollment.objects.filter(course_id=course_id, student=user).exists()


def create_review(course, user, *, rating: int, review_text: str = "") -> Review:
    # "A review can only be created by a student with a completed
    # enrollment on that course — enforced server-side" per
    # docs/07-delivery-planning/02-backend-build-milestones.md M7.
    if not _has_completed_enrollment(user, course.id):
        raise PermissionDenied("Only students who completed this course can review it.")
    if Review.objects.filter(course=course, user=user).exists():
        raise ValidationError("You have already reviewed this course — use PATCH to edit it.")
    return Review.objects.create(
        course=course, user=user, rating=rating, review_text=review_text, is_verified_purchase=True
    )


def create_discussion_post(course, user, body: str) -> CourseDiscussionPost:
    if not _has_any_enrollment(user, course.id):
        raise PermissionDenied("Only enrolled students can post in this course's discussion.")
    post = CourseDiscussionPost.objects.create(course=course, user=user, body=body)
    _broadcast_discussion_post(post)
    return post


def _broadcast_discussion_post(post: CourseDiscussionPost) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"course_{post.course_id}_discussion",
        {
            "type": "discussion.post",
            "post": {
                "id": str(post.id),
                "course_id": str(post.course_id),
                "user_id": str(post.user_id),
                "body": post.body,
                "created_at": post.created_at.isoformat(),
            },
        },
    )
