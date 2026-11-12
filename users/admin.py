from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, LoginAttempt, AuditLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Information', {'fields': ('role', 'employee_id', 'phone', 'photo', 'avatar_url', 'job_title')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile Information', {'fields': ('role', 'employee_id', 'phone', 'photo', 'avatar_url', 'job_title')}),
    )
    list_display = ('username', 'employee_id', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('username', 'ip_address', 'failed_count', 'locked_until', 'is_locked_status', 'last_attempt')
    list_filter = ('locked_until',)
    search_fields = ('username', 'ip_address')
    readonly_fields = ('last_attempt',)
    actions = ['unlock_accounts']

    @admin.display(boolean=True, description='Currently Locked')
    def is_locked_status(self, obj):
        return obj.is_locked

    @admin.action(description='Unlock selected accounts/IPs')
    def unlock_accounts(self, request, queryset):
        queryset.update(failed_count=0, locked_until=None)
        self.message_user(request, "Selected login records have been unlocked.")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'actor_username', 'actor_role', 'target_type', 'target_repr', 'ip_address')
    list_filter = ('action', 'target_type', 'actor_role', 'timestamp')
    search_fields = ('actor_username', 'target_repr', 'target_id', 'ip_address', 'action')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

    # Make strictly immutable and read-only in the admin interface
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

