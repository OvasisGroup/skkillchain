from django.urls import path

from . import views

urlpatterns = [
    path(
        "courses/<uuid:course_id>/sections/",
        views.InstructorSectionCreateView.as_view(),
        name="instructor-section-list-create",
    ),
    path(
        "sections/<uuid:section_id>/lessons/",
        views.InstructorLessonCreateView.as_view(),
        name="instructor-lesson-list-create",
    ),
    path(
        "lessons/<uuid:id>/",
        views.InstructorLessonDetailView.as_view(),
        name="instructor-lesson-detail",
    ),
]
