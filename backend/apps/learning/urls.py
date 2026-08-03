from django.urls import path

from . import views

urlpatterns = [
    path("enrollments/", views.EnrollView.as_view(), name="enroll"),
    path("students/me/courses/", views.MyCoursesView.as_view(), name="my-courses"),
    path(
        "students/me/continue-learning/",
        views.ContinueLearningView.as_view(),
        name="continue-learning",
    ),
    path(
        "courses/<uuid:course_id>/curriculum/",
        views.CourseCurriculumView.as_view(),
        name="course-curriculum",
    ),
    path("lessons/<uuid:id>/content/", views.LessonContentView.as_view(), name="lesson-content"),
    path("students/me/wishlist/", views.WishlistView.as_view(), name="wishlist"),
    path(
        "students/me/wishlist/<uuid:course_id>/",
        views.WishlistItemAddRemoveView.as_view(),
        name="wishlist-item",
    ),
    path("progress/", views.ProgressUpdateView.as_view(), name="progress-update"),
    path(
        "progress/<uuid:enrollment_id>/", views.ProgressDetailView.as_view(), name="progress-detail"
    ),
    path("lesson-notes/", views.LessonNoteCreateView.as_view(), name="lesson-note-create"),
    path("bookmarks/", views.BookmarkCreateView.as_view(), name="bookmark-create"),
    path("certificates/", views.CertificateListView.as_view(), name="certificate-list"),
    path(
        "certificates/<str:certificate_uid>/verify/",
        views.CertificateVerifyView.as_view(),
        name="certificate-verify",
    ),
]
