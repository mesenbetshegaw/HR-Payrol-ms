from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import PasswordResetToken, RegistrationRequest, SubAdminPermission, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ["email", "first_name", "last_name", "role", "is_active", "is_locked", "date_joined"]
    list_filter   = ["role", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    ordering      = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("first_name", "last_name", "phone_number", "profile_picture")}),
        ("Role", {"fields": ("role", "managed_department", "employee")}),
        ("Status", {"fields": ("is_active", "is_staff", "is_superuser", "must_change_password")}),
        ("Lockout", {"fields": ("failed_login_attempts", "lockout_until")}),
        ("Dates", {"fields": ("date_joined", "last_login")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email","first_name","last_name","role","password1","password2")}),)
    readonly_fields = ["date_joined", "last_login"]

    @admin.display(boolean=True)
    def is_locked(self, obj):
        return obj.is_locked


@admin.register(SubAdminPermission)
class SubAdminPermissionAdmin(admin.ModelAdmin):
    list_display = ["user", "module", "can_view", "can_create", "can_edit", "can_delete", "can_approve"]
    list_filter  = ["module"]
    search_fields = ["user__email"]


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "expires_at", "used"]
    readonly_fields = ["token", "created_at"]


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display  = ["email", "first_name", "last_name", "requested_role", "status", "submitted_at", "reviewed_by"]
    list_filter   = ["status", "requested_role"]
    search_fields = ["email", "first_name", "last_name"]
    readonly_fields = ["submitted_at", "updated_at", "reviewed_at", "created_user"]
    actions       = ["approve_selected", "reject_selected"]

    @admin.action(description="Approve selected registration requests")
    def approve_selected(self, request, queryset):
        from accounts.registration_services import approve_registration
        approved = 0
        for reg in queryset.filter(status="PENDING"):
            try:
                approve_registration(reg, request.user)
                approved += 1
            except Exception as e:
                self.message_user(request, f"Error approving {reg.email}: {e}", level="error")
        self.message_user(request, f"{approved} registration(s) approved.")

    @admin.action(description="Reject selected registration requests")
    def reject_selected(self, request, queryset):
        from accounts.registration_services import reject_registration
        for reg in queryset.filter(status="PENDING"):
            reject_registration(reg, request.user, "Bulk rejected by admin.")
        self.message_user(request, f"{queryset.count()} registration(s) rejected.")
