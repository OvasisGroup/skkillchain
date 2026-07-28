from django.urls import path

from . import views

urlpatterns = [
    path(
        "ai/recommendations/courses/",
        views.RecommendedCoursesView.as_view(),
        name="ai-recommendations-courses",
    ),
    path(
        "ai/recommendations/learning-paths/",
        views.LearningPathCoursesView.as_view(),
        name="ai-recommendations-learning-paths",
    ),
    path("ai/search/", views.CourseSearchView.as_view(), name="ai-search"),
]
