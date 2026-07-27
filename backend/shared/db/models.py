import uuid

from django.db import models


class UUIDPrimaryKeyModel(models.Model):
    """
    UUID primary keys for every domain model (courses, orders, etc.) so that
    resource IDs exposed in API URLs are not sequentially enumerable.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
