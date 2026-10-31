import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class TokenAuthMiddleware(MiddlewareMixin):
    """Lightweight token‑based authentication middleware.

    - Looks for an ``Authorization`` header with the format ``Bearer <token>``.
    - If ``settings.API_TOKENS`` is empty, the middleware permits all requests (useful for local dev).
    - For any request under ``/api/v1/`` the token must be present and valid.
    - Invalid or missing token results in a **401 Unauthorized** JSON response.
    """

    def process_request(self, request):
        # Only protect API endpoints; allow other paths (e.g., admin) untouched.
        if not request.path.startswith('/api/v1/'):
            return None

        # If no tokens are configured, skip authentication (dev convenience).
        if not getattr(settings, 'API_TOKENS', []):
            return None

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return self._unauthorized('Missing or malformed Authorization header')
        token = auth_header.split(' ', 1)[1].strip()
        if token not in settings.API_TOKENS:
            return self._unauthorized('Invalid API token')
        return None

    def _unauthorized(self, message: str):
        response_data = {'error': message}
        return JsonResponse(response_data, status=401)
