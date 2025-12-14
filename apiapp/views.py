
from datetime import timedelta
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from apiapp.models import *
from apiapp.serializers import *
from apiapp.utils import send_otp_email
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.mail import EmailMessage
# ===============================
# JWT Token Helpers
# ===============================
def get_tokens_for_identity(identity_id, identity_type, distributor_id=None):
    """
    identity_type should be one of: 'distributor' or 'subuser'
    This function places consistent keys into the token:
      - user_id
      - user_type
      - distributor_id (optional)
    """
    refresh = RefreshToken()
    # put conventional names into token claims
    refresh['user_id'] = identity_id
    refresh['user_type'] = identity_type
    if distributor_id:
        refresh['distributor_id'] = distributor_id
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

# ===============================
# Brnad ViewSet
# ===============================

class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

# ===============================
# Distributor ViewSet
# ===============================
class CreatedistributorViewSet(viewsets.ModelViewSet):
    queryset = CreateDistributor.objects.all()
    serializer_class = DistributorSerializer

    # Nested route: /api/v1/distributors/<pk>/subusers/
    @action(detail=True, methods=['get', 'post'])
    def subusers(self, request, pk=None):
        distributor = self.get_object()

        if request.method == 'GET':
            subusers = CreateSubUser.objects.filter(distributor=distributor)
            serializer = SubuserSerializer(subusers, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        # POST => Create new subuser for this distributor
        serializer = SubuserSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(distributor=distributor)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
# ===============================
# SubUser ViewSet
# ===============================


class DistributorSubUserViewSet(viewsets.ModelViewSet):
    serializer_class = SubuserSerializer

    def get_queryset(self):
        distributor_pk = self.kwargs.get('distributor_pk')
        return CreateSubUser.objects.filter(distributor_id=distributor_pk)

    def perform_create(self, serializer):
        distributor_pk = self.kwargs.get('distributor_pk')
        distributor = get_object_or_404(CreateDistributor, pk=distributor_pk)
        serializer.save(distributor=distributor)

# ===============================
# TyrePattern ViewSet
# ===============================

class TyrePatternViewSet(viewsets.ModelViewSet):
    serializer_class = PatternSerializer
    queryset = TyrePattern.objects.all()
    permission_classes = [AllowAny]  # ✅ No authentication required

    def get_queryset(self):
        queryset = TyrePattern.objects.all()

        # ✅ Instead of token-based brand restriction, use query parameters
        distributor_id = self.request.query_params.get('distributor_id')
        subuser_id = self.request.query_params.get('subuser_id')

        # Step 1: Restrict brands based on user type via query params
        if distributor_id:
            distributor = get_object_or_404(CreateDistributor, Company_id=distributor_id)
            allowed_brands = distributor.brands.all()
            queryset = queryset.filter(brand__in=allowed_brands)
        elif subuser_id:
            subuser = get_object_or_404(CreateSubUser, id=subuser_id)
            allowed_brands = subuser.distributor.brands.all()
            queryset = queryset.filter(brand__in=allowed_brands)

        # Step 2: Apply filters from dropdowns
        width = self.request.query_params.get('width')
        ratio = self.request.query_params.get('ratio')
        rim = self.request.query_params.get('rim')

        if width:
            queryset = queryset.filter(tyre__width=width)
        if ratio:
            queryset = queryset.filter(tyre__ratio=ratio)
        if rim:
            queryset = queryset.filter(tyre__rim=rim)

        return queryset

    def perform_create(self, serializer):
        # ✅ Keep distributor-brand restriction when creating new pattern
        distributor_id = self.request.data.get('distributor_id')
        if distributor_id:
            dist = get_object_or_404(CreateDistributor, Company_id=distributor_id)
            brand = serializer.validated_data.get('brand')
            if brand not in dist.brands.all():
                raise ValidationError("Selected brand is not assigned to your distributor")
        serializer.save()

# ===============================
# TyreModel ViewSet
# ===============================
class CreateTyreModelViewSet(viewsets.ModelViewSet):
    queryset = TyreModel.objects.all()
    serializer_class = TyreSerializer

# ===============================##############+++++++++++++



# ===============================
# Distributor Login (OTP Based)
# ===============================
# {
#   "email": "distributor@example.com"
# }

class DistributorSendOTPView(APIView):        
    def post(self, request):
        email = str(request.data.get("email")).strip()

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            distributor = CreateDistributor.objects.get(email=email)
        except CreateDistributor.DoesNotExist:
            return Response({"error": "Distributor not found"}, status=status.HTTP_404_NOT_FOUND)

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Save OTP
        distributor.otp = otp
        distributor.otp_created_at = timezone.now()
        distributor.save()

        # Send OTP Email
        subject = "Your Login OTP"
        message = f"Your OTP is: {otp}\n\nIt is valid for 5 minutes."
        print("your otp was ",{otp})

        email_msg = EmailMessage(
            subject,
            message,
            to=[email]
        )
        email_msg.send()
        

        return Response({"message": "OTP sent to your email"}, status=status.HTTP_200_OK)        


class DistributorVerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response({"error": "email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            distributor = CreateDistributor.objects.get(email=email)
        except CreateDistributor.DoesNotExist:
            return Response({"error": "Invalid email or OTP"}, status=status.HTTP_404_NOT_FOUND)

        # Check OTP match
        if distributor.otp.strip() != str(otp).strip():
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # Check OTP expiry (5 min)
        if timezone.now() > distributor.otp_created_at + timedelta(minutes=5):
            return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate JWT Token
        tokens = get_tokens_for_identity(distributor.id, "distributor", distributor_id=distributor.id)

        return Response({
            "message": "Login successful",
            "Shop_name": distributor.Shop_name,
            "email": distributor.email,
            "tokens": tokens
        }, status=status.HTTP_200_OK)
        
# -------------------------------------------------------------------
# 🔹 Distributor profile management (/me)
# -------------------------------------------------------------------
# this is not working because  ill not pass the access token properly and refresh token for now this is pospond
class DistributorMeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = request.auth

        if not token or token.get('user_type') != 'distributor':
            return Response({"error": "Sorry you are Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        distributor = get_object_or_404(CreateDistributor, id=token['user_id'])
        data = DistributorSerializer(distributor, context={'request': request}).data
        return Response(data)

    def patch(self, request):
        token = request.auth

        if not token or token.get('user_type') != 'distributor':
            return Response({"error": "Sorry you are Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        distributor = get_object_or_404(CreateDistributor, id=token['user_id'])
        serializer = DistributorSerializer(distributor, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# ===============================
# SubUser Login (Email + Password)
# ===============================
class SubUserLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        # Validate fields
        if not email or not password:
            return Response({"error": "Email and password are required"}, status=400)

        # Verify user exists
        try:
            user = CreateSubUser.objects.get(Email=email)
        except CreateSubUser.DoesNotExist:
            return Response({"error": "Invalid Email"}, status=404)

        # Check password ONLY
        if user.check_password(password):
            tokens = get_tokens_for_identity(
                identity_id=user.id,
                identity_type="subuser",
                distributor_id=user.distributor.id if user.distributor else None
            )

            return Response({
                "message": "Login successful",
                "Shop_Name": user.Shop_Name,
                "Email": user.Email,
                "tokens": tokens
            }, status=200)

        # Wrong password
        return Response({"error": "Incorrect password"}, status=400)



