from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect


class EnforceActiveUserMiddleware:
    """
    Ensures that if an authenticated user's account is deactivated (is_active=False),
    their active session is immediately terminated on their next HTTP request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_active:
            from .audit import log_audit_event
            log_audit_event(
                'SESSION_TERMINATED',
                request=request,
                actor=request.user,
                target=request.user,
                details={'reason': 'User deactivated by administrator; active session immediately revoked.'}
            )
            logout(request)
            messages.error(
                request,
                "Your account has been deactivated. Please contact an administrator."
            )
            return redirect('users:login')

        return self.get_response(request)


class SecurityHeadersMiddleware:
    """
    Appends strict modern security headers to all HTTP responses:
    - Permissions-Policy: Disables unused hardware/browser features (geolocation, camera, microphone, payment, usb)
    - Content-Security-Policy (CSP): Restricts origins for scripts, styles, fonts, and images to prevent XSS and code injection
    - Referrer-Policy: Prevents leaking URL paths or query parameters to external sites
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # 1. Disable dangerous browser hardware features
        response.headers.setdefault(
            'Permissions-Policy',
            'geolocation=(), camera=(), microphone=(), payment=(), usb=()'
        )

        # 2. Strict Referrer Policy
        response.headers.setdefault(
            'Referrer-Policy',
            'strict-origin-when-cross-origin'
        )

        # 3. Content Security Policy (tailored to Pinnacle Care Homes requirements)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.tailwindcss.com; "
            "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' https://cdn.jsdelivr.net; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers.setdefault('Content-Security-Policy', csp)

        return response

