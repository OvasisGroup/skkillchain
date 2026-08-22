import pytest

from apps.cms.models import BlogPost, BlogTag

pytestmark = pytest.mark.django_db


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create_user(email="author@example.com", password="x")


@pytest.fixture
def other_author(django_user_model):
    return django_user_model.objects.create_user(email="other-author@example.com", password="x")


def _post(author_user, *, status=BlogPost.STATUS_DRAFT, **kwargs):
    defaults = {"title": "Test Post", "body": "Body text."}
    defaults.update(kwargs)
    post = BlogPost.objects.create(author=author_user, **defaults)
    post.status = status
    if status == BlogPost.STATUS_PUBLISHED:
        from django.utils import timezone

        post.published_at = timezone.now()
    post.save(update_fields=["status", "published_at"])
    return post


class TestBlogPostListView:
    def test_lists_only_published(self, api_client, author):
        _post(author, status=BlogPost.STATUS_PUBLISHED, title="Live")
        _post(author, title="Still a Draft")

        response = api_client.get("/api/v1/blog/posts/")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == ["Live"]

    def test_filters_by_tag_slug(self, api_client, author):
        tag = BlogTag.objects.create(name="Blockchain")
        matching = _post(author, status=BlogPost.STATUS_PUBLISHED, title="Matches")
        matching.tags.add(tag)
        _post(author, status=BlogPost.STATUS_PUBLISHED, title="No Tag")

        response = api_client.get(f"/api/v1/blog/posts/?tag={tag.slug}")

        titles = [item["title"] for item in response.data["results"]]
        assert titles == ["Matches"]

    def test_response_includes_expected_fields(self, api_client, author):
        tag = BlogTag.objects.create(name="AI")
        post = _post(author, status=BlogPost.STATUS_PUBLISHED, summary="A short summary.")
        post.tags.add(tag)

        response = api_client.get("/api/v1/blog/posts/")

        item = response.data["results"][0]
        assert item["summary"] == "A short summary."
        assert item["tags"] == [{"id": str(tag.id), "name": "AI", "slug": tag.slug}]
        assert item["author"]["email"] == author.email
        assert "body" not in item


class TestBlogPostDetailView:
    def test_gets_published_post_by_slug(self, api_client, author):
        post = _post(author, status=BlogPost.STATUS_PUBLISHED, body="Full article body.")

        response = api_client.get(f"/api/v1/blog/posts/{post.slug}/")

        assert response.status_code == 200
        assert response.data["body"] == "Full article body."

    def test_draft_is_404_for_anonymous(self, api_client, author):
        post = _post(author)

        response = api_client.get(f"/api/v1/blog/posts/{post.slug}/")

        assert response.status_code == 404

    def test_draft_is_visible_to_its_author(self, api_client, author):
        post = _post(author)
        api_client.force_authenticate(user=author)

        response = api_client.get(f"/api/v1/blog/posts/{post.slug}/")

        assert response.status_code == 200

    def test_draft_is_404_for_a_different_author(self, api_client, author, other_author):
        post = _post(author)
        api_client.force_authenticate(user=other_author)

        response = api_client.get(f"/api/v1/blog/posts/{post.slug}/")

        assert response.status_code == 404


class TestBlogTagListCreateView:
    def test_list_is_public(self, api_client):
        BlogTag.objects.create(name="Web3")

        response = api_client.get("/api/v1/blog/tags/")

        assert response.status_code == 200
        assert [t["name"] for t in response.data] == ["Web3"]

    def test_create_requires_authentication(self, api_client):
        response = api_client.post("/api/v1/blog/tags/", {"name": "Web3"}, format="json")

        assert response.status_code == 401

    def test_create_is_idempotent_by_name(self, api_client, author):
        api_client.force_authenticate(user=author)

        first = api_client.post("/api/v1/blog/tags/", {"name": "Web3"}, format="json")
        second = api_client.post("/api/v1/blog/tags/", {"name": "web3"}, format="json")

        assert first.status_code == 201
        assert second.status_code == 200
        assert first.data["id"] == second.data["id"]
        assert BlogTag.objects.count() == 1


class TestAuthorBlogPostListCreateView:
    def test_lists_only_own_posts_any_status(self, api_client, author, other_author):
        _post(author, title="Mine", status=BlogPost.STATUS_PUBLISHED)
        _post(author, title="Also Mine")
        _post(other_author, title="Not Mine", status=BlogPost.STATUS_PUBLISHED)
        api_client.force_authenticate(user=author)

        response = api_client.get("/api/v1/authors/me/blog-posts/")

        titles = {item["title"] for item in response.data["results"]}
        assert titles == {"Mine", "Also Mine"}

    def test_requires_authentication(self, api_client):
        response = api_client.get("/api/v1/authors/me/blog-posts/")

        assert response.status_code == 401

    def test_create_starts_as_draft(self, api_client, author):
        api_client.force_authenticate(user=author)

        response = api_client.post(
            "/api/v1/authors/me/blog-posts/",
            {"title": "New Post", "body": "Hello world."},
            format="json",
        )

        assert response.status_code == 201
        assert response.data["status"] == "draft"
        post = BlogPost.objects.get(id=response.data["id"])
        assert post.author_id == author.id
        assert post.slug

    def test_create_with_tags(self, api_client, author):
        tag = BlogTag.objects.create(name="Careers")
        api_client.force_authenticate(user=author)

        response = api_client.post(
            "/api/v1/authors/me/blog-posts/",
            {"title": "New Post", "body": "Hello world.", "tag_ids": [str(tag.id)]},
            format="json",
        )

        assert response.status_code == 201
        post = BlogPost.objects.get(id=response.data["id"])
        assert list(post.tags.all()) == [tag]

    def test_create_without_tags_succeeds(self, api_client, author):
        api_client.force_authenticate(user=author)

        response = api_client.post(
            "/api/v1/authors/me/blog-posts/",
            {"title": "No Tags Here", "body": "Hello world."},
            format="json",
        )

        assert response.status_code == 201
        post = BlogPost.objects.get(id=response.data["id"])
        assert post.tags.count() == 0


class TestAuthorBlogPostDetailView:
    def test_owner_can_update(self, api_client, author):
        post = _post(author)
        api_client.force_authenticate(user=author)

        response = api_client.patch(
            f"/api/v1/authors/me/blog-posts/{post.id}/",
            {"title": "Updated Title"},
            format="json",
        )

        assert response.status_code == 200
        post.refresh_from_db()
        assert post.title == "Updated Title"

    def test_non_owner_is_forbidden(self, api_client, author, other_author):
        post = _post(author)
        api_client.force_authenticate(user=other_author)

        response = api_client.patch(
            f"/api/v1/authors/me/blog-posts/{post.id}/", {"title": "Nope"}, format="json"
        )

        assert response.status_code == 403

    def test_owner_can_delete(self, api_client, author):
        post = _post(author)
        api_client.force_authenticate(user=author)

        response = api_client.delete(f"/api/v1/authors/me/blog-posts/{post.id}/")

        assert response.status_code == 204
        assert not BlogPost.objects.filter(id=post.id).exists()


class TestAuthorBlogPostPublishUnpublishView:
    def test_owner_can_publish(self, api_client, author):
        post = _post(author)
        api_client.force_authenticate(user=author)

        response = api_client.post(f"/api/v1/authors/me/blog-posts/{post.id}/publish/")

        assert response.status_code == 200
        assert response.data["status"] == "published"
        post.refresh_from_db()
        assert post.published_at is not None

    def test_publishing_twice_is_rejected(self, api_client, author):
        post = _post(author, status=BlogPost.STATUS_PUBLISHED)
        api_client.force_authenticate(user=author)

        response = api_client.post(f"/api/v1/authors/me/blog-posts/{post.id}/publish/")

        assert response.status_code == 400

    def test_non_owner_cannot_publish(self, api_client, author, other_author):
        post = _post(author)
        api_client.force_authenticate(user=other_author)

        response = api_client.post(f"/api/v1/authors/me/blog-posts/{post.id}/publish/")

        assert response.status_code == 403

    def test_owner_can_unpublish(self, api_client, author):
        post = _post(author, status=BlogPost.STATUS_PUBLISHED)
        api_client.force_authenticate(user=author)

        response = api_client.post(f"/api/v1/authors/me/blog-posts/{post.id}/unpublish/")

        assert response.status_code == 200
        assert response.data["status"] == "draft"


class TestAdminBlogPostViews:
    def test_list_forbidden_without_permission(self, api_client, author):
        api_client.force_authenticate(user=author)

        response = api_client.get("/api/v1/admin/blog-posts/")

        assert response.status_code == 403

    def test_administrator_can_list_any_status_or_author(
        self, api_client, author, other_author, django_user_model
    ):
        from apps.authorization.models import Role, UserRole

        _post(author, title="Draft One")
        _post(other_author, title="Draft Two")
        admin = django_user_model.objects.create_user(email="admin@example.com", password="x")
        UserRole.objects.create(user=admin, role=Role.objects.get(code="administrator"))
        api_client.force_authenticate(user=admin)

        response = api_client.get("/api/v1/admin/blog-posts/")

        titles = {item["title"] for item in response.data["results"]}
        assert titles == {"Draft One", "Draft Two"}

    def test_administrator_can_force_unpublish(self, api_client, author, django_user_model):
        from apps.authorization.models import Role, UserRole

        post = _post(author, status=BlogPost.STATUS_PUBLISHED)
        admin = django_user_model.objects.create_user(email="admin@example.com", password="x")
        UserRole.objects.create(user=admin, role=Role.objects.get(code="administrator"))
        api_client.force_authenticate(user=admin)

        response = api_client.post(f"/api/v1/admin/blog-posts/{post.id}/unpublish/")

        assert response.status_code == 200
        assert response.data["status"] == "draft"

    def test_force_unpublish_forbidden_without_permission(self, api_client, author):
        post = _post(author, status=BlogPost.STATUS_PUBLISHED)
        api_client.force_authenticate(user=author)

        response = api_client.post(f"/api/v1/admin/blog-posts/{post.id}/unpublish/")

        assert response.status_code == 403
