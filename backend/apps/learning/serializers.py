from rest_framework import serializers

from apps.catalog.models import Course

from .models import Bookmark, Certificate, Enrollment, LessonNote, ProgressTracking, WishlistItem


class CourseSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "title", "slug", "summary"]


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseSummarySerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "course", "source", "status", "enrolled_at", "completed_at"]


class EnrollRequestSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()


class ProgressUpdateSerializer(serializers.Serializer):
    lesson_id = serializers.UUIDField()
    percent_complete = serializers.IntegerField(min_value=0, max_value=100)
    last_position_seconds = serializers.IntegerField(min_value=0, default=0)


class ProgressEntrySerializer(serializers.ModelSerializer):
    lesson_id = serializers.UUIDField(read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = ProgressTracking
        fields = [
            "lesson_id",
            "lesson_title",
            "percent_complete",
            "last_position_seconds",
            "last_viewed_at",
        ]


class EnrollmentProgressSerializer(serializers.Serializer):
    enrollment_id = serializers.UUIDField()
    status = serializers.CharField()
    overall_percent = serializers.IntegerField()
    lessons = ProgressEntrySerializer(many=True)


class LessonNoteCreateSerializer(serializers.ModelSerializer):
    lesson_id = serializers.UUIDField()

    class Meta:
        model = LessonNote
        fields = ["id", "lesson_id", "note_text", "timestamp_seconds", "created_at"]
        read_only_fields = ["id", "created_at"]


class BookmarkCreateSerializer(serializers.ModelSerializer):
    lesson_id = serializers.UUIDField()

    class Meta:
        model = Bookmark
        fields = ["id", "lesson_id", "timestamp_seconds", "label", "created_at"]
        read_only_fields = ["id", "created_at"]


class WishlistItemSerializer(serializers.ModelSerializer):
    course = CourseSummarySerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["course", "added_at"]


class CertificateSerializer(serializers.ModelSerializer):
    course = CourseSummarySerializer(source="enrollment.course", read_only=True)

    class Meta:
        model = Certificate
        fields = ["id", "certificate_uid", "course", "qr_payload", "pdf_key", "issued_at"]


class CertificateVerifyResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    certificate_uid = serializers.CharField()
    course_title = serializers.CharField()
    student_email = serializers.CharField()
    issued_at = serializers.DateTimeField()
