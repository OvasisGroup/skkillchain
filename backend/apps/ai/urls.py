from django.urls import path

from . import views

urlpatterns = [
    path(
        "ai/tutor/sessions/",
        views.AiTutorSessionCreateView.as_view(),
        name="ai-tutor-session-list-create",
    ),
    path(
        "ai/tutor/sessions/<uuid:session_id>/messages/",
        views.AiTutorMessageCreateView.as_view(),
        name="ai-tutor-message-list-create",
    ),
    path(
        "ai/assignments/<uuid:submission_id>/grade/",
        views.AIAssignmentGradeSuggestionView.as_view(),
        name="ai-assignment-grade-suggestion",
    ),
    path(
        "ai/courses/<uuid:course_id>/generate-quiz/",
        views.AiCourseGenerateQuizView.as_view(),
        name="ai-course-generate-quiz",
    ),
    path(
        "ai/lessons/<uuid:lesson_id>/generate-summary/",
        views.AiLessonGenerateSummaryView.as_view(),
        name="ai-lesson-generate-summary",
    ),
    path(
        "ai/lessons/<uuid:lesson_id>/generate-flashcards/",
        views.AiLessonGenerateFlashcardsView.as_view(),
        name="ai-lesson-generate-flashcards",
    ),
    path(
        "ai/videos/<uuid:video_id>/generate-transcript/",
        views.AiVideoGenerateTranscriptView.as_view(),
        name="ai-video-generate-transcript",
    ),
    path(
        "ai/videos/<uuid:video_id>/generate-subtitles/",
        views.AiVideoGenerateSubtitlesView.as_view(),
        name="ai-video-generate-subtitles",
    ),
    path(
        "students/me/flashcards/",
        views.StudentFlashcardsListView.as_view(),
        name="student-flashcards",
    ),
]
