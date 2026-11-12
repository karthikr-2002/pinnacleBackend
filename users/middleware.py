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
            logout(request)
            messages.error(
                request,
                "Your account has been deactivated. Please contact an administrator."
            )
            return redirect('users:login')

        return self.get_response(request)

