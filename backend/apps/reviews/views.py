from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
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


@extend_schema(tags=["Reviews"])
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


@extend_schema(tags=["Reviews"])
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


@extend_schema(tags=["Reviews"])
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
        post = services.create_discussion_post(course, request.user, serializer.validated_data["body"])
        record_event(
            actor=request.user,
            action="discussion.create",
            entity_type="CourseDiscussionPost",
            entity_id=post.id,
            request=request,
        )
        return Response(CourseDiscussionPostSerializer(post).data, status=201)
