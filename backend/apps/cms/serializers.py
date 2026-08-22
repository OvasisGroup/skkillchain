from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.identity.serializers import ProfileSerializer

from .models import BlogPost, BlogTag

User = get_user_model()


class AuthorSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    profile = ProfileSerializer(read_only=True)


class BlogTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogTag
        fields = ["id", "name", "slug"]
        read_only_fields = ["id", "slug"]


class BlogPostListSerializer(serializers.ModelSerializer):
    author = AuthorSummarySerializer(read_only=True)
    tags = BlogTagSerializer(many=True, read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "cover_image",
            "tags",
            "author",
            "status",
            "published_at",
        ]


class BlogPostDetailSerializer(serializers.ModelSerializer):
    author = AuthorSummarySerializer(read_only=True)
    tags = BlogTagSerializer(many=True, read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "body",
            "cover_image",
            "tags",
            "author",
            "status",
            "published_at",
            "created_at",
            "updated_at",
        ]


class BlogPostWriteSerializer(serializers.ModelSerializer):
    # Optional: a post can be created/edited with zero tags. Accepted as a
    # list of existing BlogTag ids — tag creation itself goes through the
    # dedicated tag endpoint, same separation as apps.catalog's Category/Tag
    # vs Course.
    tag_ids = serializers.PrimaryKeyRelatedField(
        source="tags", queryset=BlogTag.objects.all(), many=True, required=False
    )

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "body",
            "cover_image",
            "tag_ids",
            "status",
        ]
        read_only_fields = ["id", "slug", "status"]
