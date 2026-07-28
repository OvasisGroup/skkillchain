from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from apps.catalog.serializers import CourseListSerializer

from . import services


@extend_schema(tags=["Recommendations"])
class RecommendedCoursesView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return services.recommended_courses(self.request.user)


@extend_schema(tags=["Recommendations"])
class LearningPathCoursesView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return services.learning_path_courses(self.request.user)


@extend_schema(tags=["Recommendations"])
class CourseSearchView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        query = self.request.query_params.get("q", "").strip()
        if not query:
            raise ValidationError({"q": "This query parameter is required."})
        return services.search_courses(query)
