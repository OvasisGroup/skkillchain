from django.urls import path

from . import views

urlpatterns = [
    # Public
    path("blog/posts/", views.BlogPostListView.as_view(), name="blog-post-list"),
    path("blog/posts/<slug:slug>/", views.BlogPostDetailView.as_view(), name="blog-post-detail"),
    path("blog/tags/", views.BlogTagListCreateView.as_view(), name="blog-tag-list-create"),
    # Author
    path(
        "authors/me/blog-posts/",
        views.AuthorBlogPostListCreateView.as_view(),
        name="author-blog-post-list-create",
    ),
    path(
        "authors/me/blog-posts/<uuid:id>/",
        views.AuthorBlogPostDetailView.as_view(),
        name="author-blog-post-detail",
    ),
    path(
        "authors/me/blog-posts/<uuid:id>/publish/",
        views.AuthorBlogPostPublishView.as_view(),
        name="author-blog-post-publish",
    ),
    path(
        "authors/me/blog-posts/<uuid:id>/unpublish/",
        views.AuthorBlogPostUnpublishView.as_view(),
        name="author-blog-post-unpublish",
    ),
    # Moderation
    path("admin/blog-posts/", views.AdminBlogPostListView.as_view(), name="blog-post-admin-list"),
    path(
        "admin/blog-posts/<uuid:id>/",
        views.AdminBlogPostDetailView.as_view(),
        name="blog-post-admin-detail",
    ),
    path(
        "admin/blog-posts/<uuid:id>/unpublish/",
        views.AdminBlogPostUnpublishView.as_view(),
        name="blog-post-admin-unpublish",
    ),
]
