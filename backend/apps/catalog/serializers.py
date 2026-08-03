from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.identity.serializers import ProfileSerializer

from .models import Category, Course, CourseLearningObjective, CoursePrerequisite, Tag

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent"]


class CategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent"]
        read_only_fields = ["id"]
        extra_kwargs = {"slug": {"required": False}}


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


class TagWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]
        read_only_fields = ["id"]
        extra_kwargs = {"slug": {"required": False}}


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
            "cover_image",
            "price_amount",
            "currency",
            "language",
            "difficulty",
            "status",
            "published_at",
        ]


class InstructorListSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    # Annotated on the queryset (Count of owned_courses filtered to
    # published) — never present outside InstructorListView/DetailView's
    # own get_queryset(), so it's declared read_only rather than a plain
    # model field.
    published_course_count = serializers.IntegerField(read_only=True)
    categories = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "profile", "published_course_count", "categories"]

    def get_categories(self, obj) -> list:
        # Distinct categories across this instructor's published courses —
        # a course's category is optional (see Course.category), so this
        # can legitimately be empty even for an instructor with courses.
        # Reads from `_published_courses`, prefetched by
        # catalog.views._instructor_queryset(), instead of issuing a fresh
        # query per instructor (this method runs once per row in a list).
        seen = {}
        for course in obj._published_courses:
            if course.category_id and course.category_id not in seen:
                seen[course.category_id] = course.category
        return CategorySerializer(seen.values(), many=True).data


class InstructorDetailSerializer(InstructorListSerializer):
    courses = serializers.SerializerMethodField()

    class Meta(InstructorListSerializer.Meta):
        fields = InstructorListSerializer.Meta.fields + ["courses"]

    def get_courses(self, obj) -> list:
        published = sorted(
            obj._published_courses,
            key=lambda c: c.published_at.timestamp() if c.published_at else 0,
            reverse=True,
        )
        return CourseListSerializer(published, many=True).data


class CourseDetailSerializer(serializers.ModelSerializer):
    instructor = InstructorSummarySerializer(source="owner", read_only=True)
    category = CategorySerializer(read_only=True)
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
            "cover_image",
            "price_amount",
            "currency",
            "language",
            "difficulty",
            "status",
            "rejection_reason",
            "published_at",
            "category",
            "tags",
            "prerequisites",
            "learning_objectives",
            "created_at",
            "updated_at",
        ]


class CourseWriteSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source="category", queryset=Category.objects.all(), required=True
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
    cover_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "slug",
            "status",
            "title",
            "summary",
            "description",
            "cover_image",
            "language",
            "difficulty",
            "price_amount",
            "currency",
            "category_id",
            "tag_ids",
            "prerequisites",
            "learning_objectives",
        ]
        read_only_fields = ["id", "slug", "status"]

    def create(self, validated_data):
        prerequisites = validated_data.pop("prerequisites", [])
        learning_objectives = validated_data.pop("learning_objectives", [])
        tags = validated_data.pop("tags", [])

        course = Course.objects.create(owner=self.context["request"].user, **validated_data)
        course.tags.set(tags)
        self._replace_text_rows(course, prerequisites, learning_objectives)
        return course

    def update(self, instance, validated_data):
        prerequisites = validated_data.pop("prerequisites", None)
        learning_objectives = validated_data.pop("learning_objectives", None)
        tags = validated_data.pop("tags", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

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
