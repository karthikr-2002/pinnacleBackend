from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Information', {'fields': ('role', 'employee_id', 'phone', 'photo', 'avatar_url', 'job_title')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile Information', {'fields': ('role', 'employee_id', 'phone', 'photo', 'avatar_url', 'job_title')}),
    )
    list_display = ('username', 'employee_id', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
