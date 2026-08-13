from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from .models import ALLOWED_LESSON_CONTENT_EXTENSIONS, Lesson, Section


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "lesson_type",
            "sort_order",
            "duration_seconds",
            "is_preview",
            "content_file",
        ]


class SectionSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Section
        fields = ["id", "title", "sort_order", "lessons"]


class SectionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "title", "sort_order"]
        read_only_fields = ["id"]


class LessonWriteSerializer(serializers.ModelSerializer):
    # Declared explicitly (rather than relying on ModelSerializer's
    # auto-generated field) so it stays a plain optional FileField — but
    # that means the model field's validators aren't inherited automatically
    # and must be repeated here, or this endpoint would accept any file type.
    content_file = serializers.FileField(
        required=False,
        allow_null=True,
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_LESSON_CONTENT_EXTENSIONS)],
    )

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "lesson_type",
            "sort_order",
            "duration_seconds",
            "is_preview",
            "content_file",
        ]
        read_only_fields = ["id"]
