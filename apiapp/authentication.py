# apiapp/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from apiapp.models import CreateDistributor, CreateSubUser

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        user_type = validated_token.get("user_type")

        if not user_id or not user_type:
            raise AuthenticationFailed("Invalid token payload")

        # 🔹 Distributor login
        if user_type == "distributor":
            try:
                return CreateDistributor.objects.get(id=user_id)
            except CreateDistributor.DoesNotExist:
                raise AuthenticationFailed("Distributor not found")

        # 🔹 Subuser login
        elif user_type == "subuser":
            try:
                return CreateSubUser.objects.get(id=user_id)
            except CreateSubUser.DoesNotExist:
                raise AuthenticationFailed("Subuser not found")

        raise AuthenticationFailed("Invalid user type")
