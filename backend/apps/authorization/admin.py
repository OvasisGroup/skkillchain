from django.contrib import admin

from .models import Permission, Role, RolePermission, UserRole


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["resource", "action"]
    search_fields = ["resource", "action"]


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "scope"]
    search_fields = ["name", "code"]
    inlines = [RolePermissionInline]


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "context_type", "context_id"]
    search_fields = ["user__email", "role__name"]
    autocomplete_fields = ["user", "role"]
