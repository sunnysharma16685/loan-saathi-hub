import jwt
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class SupabaseAuthMiddleware(MiddlewareMixin):
"""Attach Supabase JWT user info to request.
Sets request.supabase_user, request.user_id, request.supabase_claims
"""


def process_request(self, request):
token = self._get_token(request)
request.supabase_user = None
request.user_id = None
request.supabase_claims = None
request._auth_error = None


if not token:
return
try:
claims = jwt.decode(
token,
settings.SUPABASE_JWT_SECRET,
algorithms=["HS256"],
audience="authenticated",
options={"verify_aud": True},
)
request.supabase_claims = claims
request.user_id = claims.get("sub")
request.supabase_user = {
"id": claims.get("sub"),
"email": claims.get("email"),
"role": claims.get("role"),
}
except jwt.ExpiredSignatureError:
request._auth_error = "token_expired"
except Exception:
request._auth_error = "token_invalid"


def _get_token(self, request):
auth = request.META.get("HTTP_AUTHORIZATION", "")
if auth.startswith("Bearer "):
return auth.split(" ", 1)[1].strip()
return request.COOKIES.get(getattr(settings, "SUPABASE_ACCESS_COOKIE", "sb-access-token"))