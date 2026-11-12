import logging
from django.utils import timezone
from .models import AuditLog
from .security import get_client_ip

logger = logging.getLogger(__name__)


def log_audit_event(
    action,
    request=None,
    actor=None,
    target=None,
    target_repr='',
    details=None,
    ip_address=None
):
    """
    Safely records an immutable audit entry in the AuditLog.

    Parameters:
    - action: Identifier string matching AuditLog.ACTION_CHOICES (e.g. 'USER_CREATED', 'LOGIN_FAILED')
    - request: Optional Django HttpRequest to extract actor, IP address, and User-Agent
    - actor: Optional User instance. If not provided, extracted from request.user if authenticated
    - target: Optional target model instance (e.g. User, Evaluation, Unit)
    - target_repr: Human-readable description of target (defaults to str(target))
    - details: Optional dictionary containing context or before/after attributes
    - ip_address: Optional explicit IP string (defaults to extracting from request)
    """
    try:
        # Determine Actor
        if actor is None and request and hasattr(request, 'user') and request.user.is_authenticated:
            actor = request.user

        if actor and getattr(actor, 'is_authenticated', False):
            actor_username = getattr(actor, 'username', 'System')
            actor_role = getattr(actor, 'role', '')
        else:
            actor_username = 'Anonymous' if request else 'System'
            actor_role = ''

        # Determine IP Address & User Agent
        if not ip_address and request:
            ip_address = get_client_ip(request)
        ip_address = ip_address or '127.0.0.1'

        user_agent = ''
        if request:
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

        # Determine Target
        target_type = ''
        target_id = ''
        if target:
            target_type = target.__class__.__name__
            target_id = str(getattr(target, 'pk', '') or '')
            if not target_repr:
                target_repr = str(target)[:255]
        elif not target_repr:
            target_repr = ''

        # Prepare details JSON
        safe_details = details if isinstance(details, dict) else {}

        # Persist audit record
        return AuditLog.objects.create(
            actor=actor if actor and getattr(actor, 'pk', None) else None,
            actor_username=actor_username,
            actor_role=actor_role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_repr=target_repr[:255],
            details=safe_details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        logger.exception("Audit log recording error for action '%s': %s", action, e)
        return None

