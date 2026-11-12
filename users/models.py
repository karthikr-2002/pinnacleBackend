from django.contrib.auth.models import AbstractUser
from django.db import models
from django.dispatch import receiver
from .image_security import (
    scramble_photo_filename,
    validate_image_file,
    cleanup_old_photo_file,
)


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
    photo = models.ImageField(
        upload_to=scramble_photo_filename,
        validators=[validate_image_file],
        blank=True,
        null=True
    )
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


class AuditLog(models.Model):
    """
    Immutable audit trail for compliance, transparency, and accountability across Pinnacle Care Homes.
    Captures who performed the action, from what IP, against what target, and what was modified.
    """
    ACTION_CHOICES = (
        ('LOGIN_SUCCESS', 'User Signed In'),
        ('LOGIN_FAILED', 'Failed Sign-in Attempt'),
        ('LOGIN_LOCKED', 'Account Locked Out'),
        ('LOGOUT', 'User Signed Out'),
        ('SESSION_TERMINATED', 'Session Terminated'),
        ('USER_CREATED', 'Employee Account Created'),
        ('USER_UPDATED', 'Employee Profile Updated'),
        ('USER_STATUS_CHANGED', 'Employee Status Changed'),
        ('PASSWORD_RESET', 'Password Reset by Admin'),
        ('PASSWORD_CHANGED', 'Password Changed by User'),
        ('UNIT_CREATED', 'Care Unit Created'),
        ('UNIT_UPDATED', 'Care Unit Updated'),
        ('TEMPLATE_CREATED', 'Template Created'),
        ('TEMPLATE_UPDATED', 'Template Updated'),
        ('EVALUATION_CREATED', 'Evaluation Created'),
        ('RATING_SUBMITTED', 'Peer Review Rating Submitted'),
    )

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    actor_username = models.CharField(max_length=150, db_index=True)
    actor_role = models.CharField(max_length=50, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    target_type = models.CharField(max_length=100, blank=True, db_index=True)
    target_id = models.CharField(max_length=100, blank=True)
    target_repr = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.CharField(max_length=45, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['actor_username', 'timestamp']),
            models.Index(fields=['target_type', 'target_id']),
        ]

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.actor_username} - {self.action} on {self.target_repr or self.target_type}"


# ==============================================================================
# AUTOMATIC ORPHANED FILE CLEANUP SIGNALS
# ==============================================================================

@receiver(models.signals.pre_save, sender=User)
def auto_delete_photo_on_change(sender, instance, **kwargs):
    """
    Deletes superseded photo file from disk when a user replaces or removes
    their profile photo, preventing accumulation of orphaned media files.
    """
    if not instance.pk:
        return
    try:
        old_user = User.objects.filter(pk=instance.pk).first()
        if not old_user or not old_user.photo:
            return
        if old_user.photo != instance.photo:
            cleanup_old_photo_file(old_user.photo)
    except Exception:
        pass


@receiver(models.signals.post_delete, sender=User)
def auto_delete_photo_on_delete(sender, instance, **kwargs):
    """Deletes photo file from disk when user record is permanently removed."""
    if instance.photo:
        cleanup_old_photo_file(instance.photo)

