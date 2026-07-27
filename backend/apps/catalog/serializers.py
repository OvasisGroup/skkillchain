from rest_framework import serializers

from .models import Category, Course, CourseLearningObjective, CoursePrerequisite, Tag


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent"]


class PreviewLessonSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    duration_seconds = serializers.IntegerField()


class CoursePreviewSectionSerializer(serializers.Serializer):
    section = serializers.CharField()
    lessons = PreviewLessonSerializer(many=True)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class InstructorSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()


class CourseListSerializer(serializers.ModelSerializer):
    instructor = InstructorSummarySerializer(source="owner", read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "instructor",
            "price_amount",
            "currency",
            "language",
            "difficulty",
            "status",
            "published_at",
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    instructor = InstructorSummarySerializer(source="owner", read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    prerequisites = serializers.SlugRelatedField(many=True, read_only=True, slug_field="text")
    learning_objectives = serializers.SlugRelatedField(many=True, read_only=True, slug_field="text")

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "description",
            "instructor",
            "price_amount",
            "currency",
            "language",
            "difficulty",
            "status",
            "rejection_reason",
            "published_at",
            "categories",
            "tags",
            "prerequisites",
            "learning_objectives",
            "created_at",
            "updated_at",
        ]


class CourseWriteSerializer(serializers.ModelSerializer):
    category_ids = serializers.PrimaryKeyRelatedField(
        source="categories", queryset=Category.objects.all(), many=True, required=False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        source="tags", queryset=Tag.objects.all(), many=True, required=False
    )
    # write_only: these names collide with Course's real reverse-FK related
    # managers (course.prerequisites / course.learning_objectives), so
    # without this DRF tries to serialize the RelatedManager itself as a
    # list on the way back out and crashes.
    prerequisites = serializers.ListField(
        child=serializers.CharField(), required=False, write_only=True
    )
    learning_objectives = serializers.ListField(
        child=serializers.CharField(), required=False, write_only=True
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "slug",
            "status",
            "title",
            "summary",
            "description",
            "language",
            "difficulty",
            "price_amount",
            "currency",
            "category_ids",
            "tag_ids",
            "prerequisites",
            "learning_objectives",
        ]
        read_only_fields = ["id", "slug", "status"]

    def create(self, validated_data):
        prerequisites = validated_data.pop("prerequisites", [])
        learning_objectives = validated_data.pop("learning_objectives", [])
        categories = validated_data.pop("categories", [])
        tags = validated_data.pop("tags", [])

        course = Course.objects.create(owner=self.context["request"].user, **validated_data)
        course.categories.set(categories)
        course.tags.set(tags)
        self._replace_text_rows(course, prerequisites, learning_objectives)
        return course

    def update(self, instance, validated_data):
        prerequisites = validated_data.pop("prerequisites", None)
        learning_objectives = validated_data.pop("learning_objectives", None)
        categories = validated_data.pop("categories", None)
        tags = validated_data.pop("tags", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if categories is not None:
            instance.categories.set(categories)
        if tags is not None:
            instance.tags.set(tags)
        if prerequisites is not None or learning_objectives is not None:
            self._replace_text_rows(instance, prerequisites or [], learning_objectives or [])
        return instance

    @staticmethod
    def _replace_text_rows(course, prerequisites, learning_objectives):
        if prerequisites:
            course.prerequisites.all().delete()
            CoursePrerequisite.objects.bulk_create(
                [CoursePrerequisite(course=course, text=text) for text in prerequisites]
            )
        if learning_objectives:
            course.learning_objectives.all().delete()
            CourseLearningObjective.objects.bulk_create(
                [CourseLearningObjective(course=course, text=text) for text in learning_objectives]
            )


class CourseRejectSerializer(serializers.Serializer):
    reason = serializers.CharField()
