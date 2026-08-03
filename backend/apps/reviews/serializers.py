from rest_framework import serializers

from .models import CourseDiscussionPost, Review


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "id",
            "course",
            "user",
            "rating",
            "review_text",
            "is_verified_purchase",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["is_verified_purchase"]


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    review_text = serializers.CharField(required=False, allow_blank=True, default="")


class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["rating", "review_text"]
        extra_kwargs = {"rating": {"required": False}, "review_text": {"required": False}}


class CourseDiscussionPostSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = CourseDiscussionPost
        fields = ["id", "course", "user", "user_email", "body", "created_at"]


class CourseDiscussionPostCreateSerializer(serializers.Serializer):
    body = serializers.CharField(allow_blank=False)
