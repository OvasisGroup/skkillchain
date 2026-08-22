from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.authorization.permissions import HasPermission
from shared.api.pagination import DefaultCursorPagination, PublishedAtCursorPagination

from .models import BlogPost, BlogTag, InvalidBlogPostTransition
from .serializers import (
    BlogPostDetailSerializer,
    BlogPostListSerializer,
    BlogPostWriteSerializer,
    BlogTagSerializer,
)

_LIST_FIELDS_QUERYSET = BlogPost.objects.select_related(
    "author", "author__profile"
).prefetch_related("tags")


def _owned_post_or_403(post_id, user):
    post = get_object_or_404(_LIST_FIELDS_QUERYSET, pk=post_id)
    if post.author_id != user.id:
        raise PermissionDenied("You do not own this blog post.")
    return post


_BLOG_POST_EXAMPLE = {
    "id": "1c2d3e4f-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
    "title": "5 Ways to Learn Blockchain Faster",
    "slug": "5-ways-to-learn-blockchain-faster",
    "summary": "Practical habits that cut the learning curve without cutting corners.",
    "cover_image": None,
    "tags": [{"id": "9a8b7c6d-...", "name": "Blockchain", "slug": "blockchain"}],
    "author": {
        "id": "b6a5b6c0-9b1e-4c9a-9b7a-1f2e3d4c5b6a",
        "email": "team@skillchain.example",
        "profile": {"first_name": "Amaka", "last_name": "Obi"},
    },
    "status": "published",
    "published_at": "2026-02-01T00:00:00Z",
}


# ---------- Public reading ----------


@extend_schema(
    tags=["Blog"],
    parameters=[OpenApiParameter("tag", str, description="Filter by a tag's slug.")],
    description="Lists published blog posts, newest first. Optionally filter to one tag.",
    examples=[OpenApiExample("Blog post", value=_BLOG_POST_EXAMPLE, response_only=True)],
)
class BlogPostListView(generics.ListAPIView):
    serializer_class = BlogPostListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = PublishedAtCursorPagination

    def get_queryset(self):
        qs = _LIST_FIELDS_QUERYSET.filter(status=BlogPost.STATUS_PUBLISHED)
        if tag_slug := self.request.query_params.get("tag"):
            qs = qs.filter(tags__slug=tag_slug)
        return qs


@extend_schema(
    tags=["Blog"],
    description="Gets a published blog post by slug. The author can also see their own draft "
    "through this same endpoint; anyone else gets a 404, identical to a nonexistent post.",
    examples=[
        OpenApiExample(
            "Blog post detail",
            value={
                **_BLOG_POST_EXAMPLE,
                "body": "Full article body...",
                "created_at": "2026-01-20T00:00:00Z",
                "updated_at": "2026-01-20T00:00:00Z",
            },
            response_only=True,
        )
    ],
)
class BlogPostDetailView(generics.RetrieveAPIView):
    serializer_class = BlogPostDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_object(self):
        post = get_object_or_404(_LIST_FIELDS_QUERYSET, slug=self.kwargs["slug"])
        is_author = self.request.user.is_authenticated and post.author_id == self.request.user.id
        if post.status != BlogPost.STATUS_PUBLISHED and not is_author:
            raise NotFound("No blog post found matching the query.")
        return post


@extend_schema_view(
    get=extend_schema(tags=["Blog"], description="Lists all blog tags."),
    post=extend_schema(
        tags=["Blog"],
        description="Creates a tag, or returns the existing one if a tag with the same name "
        "(case-insensitive) already exists — any authenticated author can add a tag inline "
        "while writing a post, so this is idempotent rather than erroring on a duplicate name. "
        "Same pattern as apps.catalog's course-tag endpoint.",
        examples=[OpenApiExample("Create", value={"name": "Web3"}, request_only=True)],
    ),
)
class BlogTagListCreateView(generics.ListAPIView):
    serializer_class = BlogTagSerializer
    queryset = BlogTag.objects.all()
    pagination_class = None

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def post(self, request, *args, **kwargs):
        name = (request.data.get("name") or "").strip()
        if not name:
            raise ValidationError({"name": ["This field is required."]})

        tag = BlogTag.objects.filter(name__iexact=name).first()
        if tag is not None:
            return Response(BlogTagSerializer(tag).data)

        tag = BlogTag.objects.create(name=name)
        return Response(BlogTagSerializer(tag).data, status=201)


# ---------- Author: write and manage own posts ----------


@extend_schema(
    tags=["BlogAuthor"],
    description="Lists blog posts written by the current user, any status, most recently "
    "created first.",
)
class AuthorBlogPostListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultCursorPagination

    def get_queryset(self):
        return _LIST_FIELDS_QUERYSET.filter(author=self.request.user)

    def get_serializer_class(self):
        return BlogPostListSerializer if self.request.method == "GET" else BlogPostWriteSerializer

    @extend_schema(
        tags=["BlogAuthor"],
        request=BlogPostWriteSerializer,
        responses={201: BlogPostWriteSerializer},
        description="Creates a new blog post. Starts as a draft — call the publish endpoint "
        "to make it visible on the public blog.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)
        record_event(
            actor=self.request.user,
            action="blog_post.create",
            entity_type="BlogPost",
            entity_id=post.id,
            request=self.request,
        )


@extend_schema(
    tags=["BlogAuthor"],
    description="Gets, updates, or deletes a blog post the current user wrote.",
)
class AuthorBlogPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BlogPostWriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return _owned_post_or_403(self.kwargs["id"], self.request.user)

    def perform_destroy(self, instance):
        post_id = instance.id
        instance.delete()
        record_event(
            actor=self.request.user,
            action="blog_post.delete",
            entity_type="BlogPost",
            entity_id=post_id,
            request=self.request,
        )


def _transition_or_409(post, method_name):
    try:
        getattr(post, method_name)()
    except InvalidBlogPostTransition as exc:
        raise ValidationError(str(exc)) from exc


@extend_schema(
    tags=["BlogAuthor"],
    request=None,
    responses={200: BlogPostListSerializer},
    description="Publishes a draft blog post the current user wrote, making it visible on the "
    "public blog.",
)
class AuthorBlogPostPublishView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        post = _owned_post_or_403(id, request.user)
        _transition_or_409(post, "publish")
        record_event(
            actor=request.user,
            action="blog_post.publish",
            entity_type="BlogPost",
            entity_id=post.id,
            request=request,
        )
        return Response(BlogPostListSerializer(post).data)


@extend_schema(
    tags=["BlogAuthor"],
    request=None,
    responses={200: BlogPostListSerializer},
    description="Unpublishes a blog post the current user wrote, taking it back to draft.",
)
class AuthorBlogPostUnpublishView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        post = _owned_post_or_403(id, request.user)
        _transition_or_409(post, "unpublish")
        record_event(
            actor=request.user,
            action="blog_post.unpublish",
            entity_type="BlogPost",
            entity_id=post.id,
            request=request,
        )
        return Response(BlogPostListSerializer(post).data)


# ---------- Moderation override ----------


@extend_schema(
    tags=["Admin"],
    description="Lists every blog post on the platform, any status or author — the moderation "
    "counterpart to the author's own (self-scoped) list endpoint.",
)
class AdminBlogPostListView(generics.ListAPIView):
    serializer_class = BlogPostListSerializer
    permission_classes = [HasPermission]
    required_permission = "cms.manage"
    throttle_scope = "admin-write"
    queryset = _LIST_FIELDS_QUERYSET.order_by("-created_at")


@extend_schema(
    tags=["Admin"],
    description="Gets or updates any blog post regardless of author — for platform moderation, "
    "not the author's own self-service editing.",
)
class AdminBlogPostDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = BlogPostWriteSerializer
    permission_classes = [HasPermission]
    required_permission = "cms.manage"
    throttle_scope = "admin-write"
    queryset = BlogPost.objects.all()
    lookup_url_kwarg = "id"

    def perform_update(self, serializer):
        post = serializer.save()
        record_event(
            actor=self.request.user,
            action="blog_post.admin_update",
            entity_type="BlogPost",
            entity_id=post.id,
            request=self.request,
        )


@extend_schema(
    tags=["Admin"],
    request=None,
    responses={200: BlogPostListSerializer},
    description="Force-unpublishes any blog post — for platform moderation, not the author's "
    "own controls.",
)
class AdminBlogPostUnpublishView(APIView):
    permission_classes = [HasPermission]
    required_permission = "cms.manage"
    throttle_scope = "admin-write"

    def post(self, request, id):
        post = get_object_or_404(BlogPost, pk=id)
        _transition_or_409(post, "unpublish")
        record_event(
            actor=request.user,
            action="blog_post.admin_unpublish",
            entity_type="BlogPost",
            entity_id=post.id,
            request=request,
        )
        return Response(BlogPostListSerializer(post).data)
