from django.urls import path

from . import views

urlpatterns = [
    path("courses/", views.CourseListView.as_view(), name="course-list"),
    path("courses/<uuid:id>/", views.CourseDetailView.as_view(), name="course-detail"),
    path("courses/<uuid:id>/preview/", views.CoursePreviewView.as_view(), name="course-preview"),
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("tags/", views.TagListView.as_view(), name="tag-list"),
    path(
        "instructor/courses/",
        views.InstructorCourseListCreateView.as_view(),
        name="instructor-course-list-create",
    ),
    path(
        "instructor/courses/<uuid:id>/",
        views.InstructorCourseDetailView.as_view(),
        name="instructor-course-detail",
    ),
    path(
        "instructor/courses/<uuid:id>/submit-review/",
        views.CourseSubmitReviewView.as_view(),
        name="course-submit-review",
    ),
    path(
        "instructor/courses/<uuid:id>/publish/",
        views.CoursePublishView.as_view(),
        name="course-publish",
    ),
    path(
        "admin/courses/pending-review/",
        views.CoursesPendingReviewView.as_view(),
        name="courses-pending-review",
    ),
    path(
        "admin/courses/<uuid:id>/approve/", views.CourseApproveView.as_view(), name="course-approve"
    ),
    path("admin/courses/<uuid:id>/reject/", views.CourseRejectView.as_view(), name="course-reject"),
]
