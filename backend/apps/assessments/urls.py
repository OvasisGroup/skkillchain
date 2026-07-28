from django.urls import path

from . import views

urlpatterns = [
    path(
        "instructor/courses/<uuid:course_id>/quizzes/",
        views.InstructorQuizCreateView.as_view(),
        name="instructor-quiz-create",
    ),
    path(
        "instructor/courses/<uuid:course_id>/assignments/",
        views.InstructorAssignmentCreateView.as_view(),
        name="instructor-assignment-create",
    ),
    path(
        "instructor/courses/<uuid:course_id>/coding-exercises/",
        views.InstructorCodingExerciseCreateView.as_view(),
        name="instructor-coding-exercise-create",
    ),
    path(
        "instructor/assignments/<uuid:id>/submissions/",
        views.InstructorAssignmentSubmissionsListView.as_view(),
        name="instructor-assignment-submissions",
    ),
    path(
        "instructor/assignments/<uuid:id>/submissions/<uuid:submission_id>/grade/",
        views.InstructorAssignmentGradeView.as_view(),
        name="instructor-assignment-grade",
    ),
    path("quizzes/<uuid:id>/", views.QuizDetailView.as_view(), name="quiz-detail"),
    path(
        "quizzes/<uuid:id>/attempts/",
        views.QuizAttemptStartView.as_view(),
        name="quiz-attempt-start",
    ),
    path("quizzes/<uuid:id>/submit/", views.QuizSubmitView.as_view(), name="quiz-submit"),
    path(
        "assignments/<uuid:id>/submissions/",
        views.AssignmentSubmissionCreateView.as_view(),
        name="assignment-submission-create",
    ),
    path("students/me/grades/", views.MyGradesView.as_view(), name="my-grades"),
    path(
        "coding-exercises/<uuid:id>/",
        views.CodingExerciseDetailView.as_view(),
        name="coding-exercise-detail",
    ),
    path(
        "coding-exercises/<uuid:id>/submissions/",
        views.CodingExerciseSubmissionCreateView.as_view(),
        name="coding-exercise-submission-create",
    ),
    path(
        "coding-exercises/<uuid:id>/submissions/<uuid:submission_id>/",
        views.CodingExerciseSubmissionDetailView.as_view(),
        name="coding-exercise-submission-detail",
    ),
]
