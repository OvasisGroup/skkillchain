from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import MFAFactor, OAuthIdentity, Profile, User


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-created_at"]
    list_display = ["email", "is_staff", "is_active", "created_at"]
    search_fields = ["email"]
    readonly_fields = ["created_at", "updated_at", "last_login"]
    inlines = [ProfileInline]

    def get_inline_instances(self, request, obj=None):
        # The identity.signals post_save hook creates the Profile row once the
        # user exists; showing the inline on the "add user" form (before that
        # row exists) makes Django's inline formset try to INSERT a second
        # Profile with the same PK and crash. Only show it once obj is real.
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)


@admin.register(OAuthIdentity)
class OAuthIdentityAdmin(admin.ModelAdmin):
    list_display = ["user", "provider", "provider_user_id", "created_at"]
    list_filter = ["provider"]
    search_fields = ["user__email", "provider_user_id"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(MFAFactor)
class MFAFactorAdmin(admin.ModelAdmin):
    list_display = ["user", "factor_type", "is_primary", "confirmed_at", "created_at"]
    list_filter = ["factor_type"]
    search_fields = ["user__email"]
    # secret_encrypted is deliberately never shown, even encrypted — no
    # reason for it to appear anywhere in the admin UI.
    readonly_fields = ["id", "created_at", "updated_at", "confirmed_at"]
    exclude = ["secret_encrypted"]
