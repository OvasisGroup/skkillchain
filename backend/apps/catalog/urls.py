from django.urls import path

from . import views

urlpatterns = [
    path("courses/", views.CourseListView.as_view(), name="course-list"),
    path("courses/<uuid:id>/", views.CourseDetailView.as_view(), name="course-detail"),
    path("courses/<uuid:id>/preview/", views.CoursePreviewView.as_view(), name="course-preview"),
    path("categories/", views.CategoryListCreateView.as_view(), name="category-list-create"),
    path("categories/<uuid:id>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("tags/", views.TagListCreateView.as_view(), name="tag-list-create"),
    path("tags/<uuid:id>/", views.TagDetailView.as_view(), name="tag-detail"),
    path("instructors/", views.InstructorListView.as_view(), name="instructor-list"),
    path("instructors/<uuid:id>/", views.InstructorDetailView.as_view(), name="instructor-detail"),
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
    path("admin/courses/", views.AdminCourseListView.as_view(), name="admin-course-list-create"),
    path(
        "admin/courses/<uuid:id>/",
        views.AdminCourseDetailView.as_view(),
        name="admin-course-detail",
    ),
    path(
        "admin/courses/<uuid:id>/notify/",
        views.AdminCourseNotifyView.as_view(),
        name="admin-course-notify",
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
