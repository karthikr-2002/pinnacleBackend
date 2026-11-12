from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, LoginAttempt


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

