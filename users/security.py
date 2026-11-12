import math
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from .models import LoginAttempt


def get_client_ip(request):
    """Safely extract client IP address handling potential reverse proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain (original client)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip or '127.0.0.1'


def get_max_failed_attempts():
    return getattr(settings, 'LOGIN_MAX_FAILED_ATTEMPTS', 5)


def get_lockout_duration():
    return getattr(settings, 'LOGIN_LOCKOUT_DURATION', 900)  # 15 minutes


def get_ip_max_failed_attempts():
    return getattr(settings, 'IP_MAX_FAILED_ATTEMPTS', 15)


def check_login_lockout(username, ip_address):
    """
    Checks if an account or IP is currently locked out.
    Returns: (is_locked: bool, remaining_minutes: int, remaining_seconds: int, reason: str)
    """
    now = timezone.now()
    clean_username = (username or '').strip().lower()

    # 1. Check account-specific lockout
    if clean_username:
        attempt = LoginAttempt.objects.filter(username__iexact=clean_username, ip_address=ip_address).first()
        if attempt and attempt.locked_until:
            if attempt.locked_until > now:
                remaining_secs = int((attempt.locked_until - now).total_seconds())
                remaining_mins = max(1, math.ceil(remaining_secs / 60))
                return True, remaining_mins, remaining_secs, "account"
            else:
                # Lockout has expired; reset
                attempt.failed_count = 0
                attempt.locked_until = None
                attempt.save(update_fields=['failed_count', 'locked_until'])

    # 2. Check IP-wide brute-force lockout (protection against dictionary/spraying attacks)
    ip_attempts = LoginAttempt.objects.filter(ip_address=ip_address)
    ip_locked = ip_attempts.filter(locked_until__gt=now).order_by('-locked_until').first()
    if ip_locked:
        remaining_secs = int((ip_locked.locked_until - now).total_seconds())
        remaining_mins = max(1, math.ceil(remaining_secs / 60))
        return True, remaining_mins, remaining_secs, "network IP"

    return False, 0, 0, ""


def record_login_failure(username, ip_address):
    """
    Increments failed login count for this username and IP.
    Applies lockout if threshold is exceeded.
    Returns: (is_locked: bool, remaining_attempts: int, remaining_minutes: int)
    """
    now = timezone.now()
    clean_username = (username or '').strip().lower()
    max_attempts = get_max_failed_attempts()
    lockout_secs = get_lockout_duration()

    attempt, _ = LoginAttempt.objects.get_or_create(
        username=clean_username,
        ip_address=ip_address,
        defaults={'failed_count': 0}
    )

    # If previous lockout expired, start fresh
    if attempt.locked_until and attempt.locked_until <= now:
        attempt.failed_count = 0
        attempt.locked_until = None

    attempt.failed_count += 1

    if attempt.failed_count >= max_attempts:
        attempt.locked_until = now + timedelta(seconds=lockout_secs)
        attempt.save(update_fields=['failed_count', 'locked_until'])
        remaining_mins = max(1, math.ceil(lockout_secs / 60))
        return True, 0, remaining_mins

    attempt.save(update_fields=['failed_count'])
    remaining_attempts = max(0, max_attempts - attempt.failed_count)
    return False, remaining_attempts, 0


def record_login_success(username, ip_address):
    """Clears any failed login counter on successful sign-in."""
    clean_username = (username or '').strip().lower()
    LoginAttempt.objects.filter(username__iexact=clean_username, ip_address=ip_address).delete()

