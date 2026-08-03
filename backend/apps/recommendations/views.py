from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from apps.catalog.serializers import CourseListSerializer

from . import services

_RECOMMENDED_COURSE_EXAMPLE = {
    "id": "1c2d3e4f-...",
    "title": "Complete Python Bootcamp",
    "slug": "complete-python-bootcamp",
    "summary": "Learn Python from scratch, from syntax to real projects.",
    "instructor": {"id": "b6a5b6c0-...", "email": "jane@example.com"},
    "price_amount": "49.99",
    "currency": "USD",
    "language": "en",
    "difficulty": "beginner",
    "status": "published",
    "published_at": "2026-01-10T12:00:00Z",
}


@extend_schema(
    tags=["Recommendations"],
    description="Lists courses recommended for the current user, based on their enrollment "
    "and category history.",
    examples=[OpenApiExample("Course", value=_RECOMMENDED_COURSE_EXAMPLE, response_only=True)],
)
class RecommendedCoursesView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return services.recommended_courses(self.request.user)


@extend_schema(
    tags=["Recommendations"],
    description="Lists courses forming a suggested learning path for the current user (e.g. "
    "the next course in a category they're progressing through).",
    examples=[OpenApiExample("Course", value=_RECOMMENDED_COURSE_EXAMPLE, response_only=True)],
)
class LearningPathCoursesView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return services.learning_path_courses(self.request.user)


@extend_schema(
    tags=["Recommendations"],
    parameters=[OpenApiParameter("q", str, required=True, description="Free-text search query.")],
    description="Public course search by free-text query across title/summary.",
    examples=[OpenApiExample("Course", value=_RECOMMENDED_COURSE_EXAMPLE, response_only=True)],
)
class CourseSearchView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip()
        if not query:
            raise ValidationError({"q": ["This query parameter is required."]})
        return services.search_courses(query)
