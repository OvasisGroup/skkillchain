from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import generics, mixins, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.audit.services import record_event
from apps.catalog.models import Course

from . import services
from .models import CourseDiscussionPost, Review
from .serializers import (
    CourseDiscussionPostCreateSerializer,
    CourseDiscussionPostSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
    ReviewUpdateSerializer,
)

_REVIEW_EXAMPLE = {
    "id": "b8c9d0e1-...",
    "course": "1c2d3e4f-...",
    "user": "b6a5b6c0-...",
    "rating": 5,
    "review_text": "Clear explanations and great pacing.",
    "is_verified_purchase": True,
    "created_at": "2026-02-01T12:00:00Z",
    "updated_at": "2026-02-01T12:00:00Z",
}


@extend_schema_view(
    get=extend_schema(
        tags=["Reviews"],
        description="Lists reviews for a course — public, no authentication required.",
        examples=[OpenApiExample("Review", value=_REVIEW_EXAMPLE, response_only=True)],
    ),
    post=extend_schema(
        tags=["Reviews"],
        description="Posts a review for a course. Only students with a completed enrollment "
        "may review it (so is_verified_purchase is always true); one review per user per "
        "course — PATCH the existing one instead of re-posting.",
        examples=[
            OpenApiExample(
                "Create review",
                value={"rating": 5, "review_text": "Clear explanations and great pacing."},
                request_only=True,
            ),
            OpenApiExample("Created", value=_REVIEW_EXAMPLE, response_only=True),
        ],
    ),
)
class CourseReviewListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        # Reviews are public reading material for prospective students
        # (same AllowAny-for-GET philosophy as apps.catalog.views course
        # browsing) — only writing one requires auth.
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        return ReviewCreateSerializer if self.request.method == "POST" else ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(course_id=self.kwargs["course_id"]).select_related("user")

    def create(self, request, *args, **kwargs):
        course = get_object_or_404(Course, id=self.kwargs["course_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = services.create_review(
            course,
            request.user,
            rating=serializer.validated_data["rating"],
            review_text=serializer.validated_data["review_text"],
        )
        record_event(
            actor=request.user,
            action="review.create",
            entity_type="Review",
            entity_id=review.id,
            request=request,
        )
        return Response(ReviewSerializer(review).data, status=201)


@extend_schema_view(
    patch=extend_schema(
        tags=["Reviews"],
        description="Edits the current user's own review. 403 if it belongs to someone else.",
        examples=[
            OpenApiExample("Update rating", value={"rating": 4}, request_only=True),
            OpenApiExample("Updated", value={**_REVIEW_EXAMPLE, "rating": 4}, response_only=True),
        ],
    ),
    delete=extend_schema(
        tags=["Reviews"],
        description="Deletes the current user's own review. 403 if it belongs to someone else.",
    ),
)
class ReviewUpdateDestroyView(
    mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView
):
    queryset = Review.objects.all()
    serializer_class = ReviewUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "review_id"

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def get_object(self):
        review = get_object_or_404(Review, id=self.kwargs["review_id"])
        if review.user_id != self.request.user.id:
            raise PermissionDenied("You can only edit or delete your own review.")
        return review

    def perform_update(self, serializer):
        serializer.save()
        record_event(
            actor=self.request.user,
            action="review.update",
            entity_type="Review",
            entity_id=serializer.instance.id,
            request=self.request,
        )

    def perform_destroy(self, instance):
        record_event(
            actor=self.request.user,
            action="review.delete",
            entity_type="Review",
            entity_id=instance.id,
            request=self.request,
        )
        instance.delete()


@extend_schema_view(
    get=extend_schema(
        tags=["Reviews"],
        description="Lists discussion posts for a course — public, no authentication required.",
        examples=[
            OpenApiExample(
                "Post",
                value={
                    "id": "c9d0e1f2-...",
                    "course": "1c2d3e4f-...",
                    "user": "b6a5b6c0-...",
                    "user_email": "student@example.com",
                    "body": "Does anyone have tips for exercise 3?",
                    "created_at": "2026-02-01T13:00:00Z",
                },
                response_only=True,
            )
        ],
    ),
    post=extend_schema(
        tags=["Reviews"],
        description="Posts a discussion comment on a course. Requires the current user to be "
        "enrolled (any status, not necessarily completed).",
        examples=[
            OpenApiExample(
                "Create post",
                value={"body": "Does anyone have tips for exercise 3?"},
                request_only=True,
            )
        ],
    ),
)
class CourseDiscussionListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        return (
            CourseDiscussionPostCreateSerializer
            if self.request.method == "POST"
            else CourseDiscussionPostSerializer
        )

    def get_queryset(self):
        return CourseDiscussionPost.objects.filter(
            course_id=self.kwargs["course_id"]
        ).select_related("user")

    def create(self, request, *args, **kwargs):
        course = get_object_or_404(Course, id=self.kwargs["course_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = services.create_discussion_post(
            course, request.user, serializer.validated_data["body"]
        )
        record_event(
            actor=request.user,
            action="discussion.create",
            entity_type="CourseDiscussionPost",
            entity_id=post.id,
            request=request,
        )
        return Response(CourseDiscussionPostSerializer(post).data, status=201)
