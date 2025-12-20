from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken



class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        try:
            token_str = auth_header.split()[1]
            token = AccessToken(token_str)
        except Exception:
            raise AuthenticationFailed("Invalid token")

        # IMPORTANT: return (user, token)
        # We don't use Django User → return None
        return (None, token)