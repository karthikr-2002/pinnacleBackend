from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
        ('user', 'User'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique staff identifier used as the login username."
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    photo = models.ImageField(upload_to='employees/photos/', blank=True, null=True)
    avatar_url = models.CharField(
        max_length=500,
        blank=True,
        default='/static/images/default-avatar.png'
    )
    job_title = models.CharField(max_length=100, blank=True, default='Administrator')

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        full_name = self.get_full_name()
        if full_name:
            return full_name
        return self.username

    @property
    def status_label(self):
        return 'Active' if self.is_active else 'Inactive'

    @property
    def photo_url(self):
        if self.photo:
            try:
                return self.photo.url
            except Exception:
                pass
        if self.avatar_url and not ('dicebear.com' in self.avatar_url or 'bottts' in self.avatar_url):
            return self.avatar_url
        return '/static/images/default-avatar.png'


class LoginAttempt(models.Model):
    """Tracks failed login attempts by username and IP for brute-force protection."""
    username = models.CharField(max_length=150, db_index=True)
    ip_address = models.CharField(max_length=45, db_index=True)
    failed_count = models.PositiveIntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now=True)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('username', 'ip_address')
        indexes = [
            models.Index(fields=['username', 'ip_address']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f"{self.username} ({self.ip_address}): {self.failed_count} failures"

    @property
    def is_locked(self):
        from django.utils import timezone
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def remaining_seconds(self):
        from django.utils import timezone
        if self.is_locked:
            return max(0, int((self.locked_until - timezone.now()).total_seconds()))
        return 0

    def remaining_minutes(self):
        import math
        secs = self.remaining_seconds()
        return max(1, math.ceil(secs / 60)) if secs > 0 else 0

