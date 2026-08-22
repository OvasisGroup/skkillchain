import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from shared.db.models import TimeStampedModel


class InvalidBlogPostTransition(Exception):
    """Raised by BlogPost's publish()/unpublish() on an out-of-order status
    transition — views translate this to a 400, same as
    InvalidHackathonTransition in apps.hackathons."""


class BlogTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        db_table = "blog_tags"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        base = slugify(self.name)[:120] or "tag"
        slug = base
        suffix = 1
        while BlogTag.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            suffix += 1
            slug = f"{base}-{suffix}"
        return slug


def blog_post_cover_upload_path(instance, filename):
    return f"blog/{instance.id}/cover/{filename}"


class BlogPost(TimeStampedModel):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="blog_posts"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    # Short standfirst used as the card/list excerpt and as the prefilled
    # text for the Twitter/LinkedIn share links — kept separate from `body`
    # so a share link doesn't have to truncate raw article text.
    summary = models.CharField(max_length=300, blank=True)
    body = models.TextField()
    cover_image = models.ImageField(upload_to=blog_post_cover_upload_path, blank=True)
    # Optional by design — plenty of posts (announcements, short updates)
    # have nothing worth tagging.
    tags = models.ManyToManyField(BlogTag, blank=True, related_name="posts")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "blog_posts"
        ordering = ["-published_at", "-created_at"]
        indexes = [models.Index(fields=["status", "published_at"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        base = slugify(self.title)[:200] or "post"
        slug = base
        suffix = 1
        while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            suffix += 1
            slug = f"{base}-{suffix}"
        return slug

    # --- Lifecycle: draft <-> published ---

    def publish(self):
        if self.status == self.STATUS_PUBLISHED:
            raise InvalidBlogPostTransition("Already published")
        self.status = self.STATUS_PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])

    def unpublish(self):
        if self.status != self.STATUS_PUBLISHED:
            raise InvalidBlogPostTransition("Not currently published")
        self.status = self.STATUS_DRAFT
        self.save(update_fields=["status", "updated_at"])
