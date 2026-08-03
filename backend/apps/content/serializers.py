from rest_framework import serializers

from .models import Lesson, Section


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
    content_file = serializers.FileField(required=False, allow_null=True)

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
