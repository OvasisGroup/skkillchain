from django.urls import path

from . import views

urlpatterns = [
    path(
        "courses/<uuid:course_id>/reviews/",
        views.CourseReviewListCreateView.as_view(),
        name="course-review-list-create",
    ),
    path(
        "reviews/<uuid:review_id>/",
        views.ReviewUpdateDestroyView.as_view(),
        name="review-update-destroy",
    ),
    path(
        "courses/<uuid:course_id>/discussions/",
        views.CourseDiscussionListCreateView.as_view(),
        name="course-discussion-list-create",
    ),
]
