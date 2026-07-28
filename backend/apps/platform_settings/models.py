import uuid

from django.db import models


class Setting(models.Model):
    SCOPE_PLATFORM = "platform"
    SCOPE_CHOICES = [(SCOPE_PLATFORM, "Platform")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scope_type = models.CharField(max_length=30, choices=SCOPE_CHOICES, default=SCOPE_PLATFORM)
    scope_id = models.UUIDField(null=True, blank=True)
    key = models.CharField(max_length=150)
    value_json = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "settings"
        # NULL scope_id (platform-wide settings) isn't actually deduplicated
        # by this constraint — Postgres treats NULL as distinct from every
        # other NULL, so two rows with the same (scope_type, key) and a
        # NULL scope_id can both exist. services.upsert_setting() uses
        # update_or_create keyed on all three fields to avoid creating a
        # second row in practice; this constraint still catches org-scoped
        # duplicates (non-null scope_id), which is the case it enforces.
        constraints = [
            models.UniqueConstraint(
                fields=["scope_type", "scope_id", "key"], name="uniq_setting_scope_key"
            )
        ]

    def __str__(self):
        return f"{self.scope_type}:{self.scope_id}:{self.key}"
