
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

    # GET: createDistributor/{id}/subusers/
    @action(detail=True, methods=['get'])
    def subusers(self, request, pk=None):
        distributor = CreateDistributor.objects.get(pk=pk)
        subusers = CreateSubUser.objects.filter(Distributor_Name=distributor)
        subuser_serializer = SubuserSerializer(subusers, many=True, context={'request': request})
        return Response(subuser_serializer.data)
    
    # Override create method to add custom behavior for assigning distributor automatically using mobile number
    def create(self, request, *args, **kwargs):
        distributor_mobile = request.data.get("distributor_mobile")
        if not distributor_mobile:
            return Response({"error": "distributor_mobile is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            distributor = CreateDistributor.objects.get(mobileNo=distributor_mobile)
        except CreateDistributor.DoesNotExist:
            return Response({"error": "Distributor not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(distributor=distributor)  # 👈 Assign distributor automatically

        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ===============================
# SubUser ViewSet
# ===============================
class DistributorSubUserViewSet(viewsets.ModelViewSet):
    serializer_class = SubuserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        token = self.request.auth
        if not token or token.get("user_type") != "distributor":
            return CreateSubUser.objects.none()
        distributor_id = token["user_id"]
        return CreateSubUser.objects.filter(distributor__Company_id=distributor_id, is_active=True)

    def perform_create(self, serializer):
        token = getattr(self.request, 'auth', None) or {}
        if token.get('user_type') != 'distributor':
            raise PermissionError("Not authorized")
        distributor = get_object_or_404(CreateDistributor, Company_id=token["user_id"])
        serializer.save(distributor=distributor)  # serializer.create will handle password hashing

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

OTP_VALIDITY_MINUTES = 10
MAX_LOGIN_ATTEMPTS = 5
OTP_RESEND_INTERVAL_SECONDS = 30
class DistributorSendOTPView(APIView):
        
    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            distributor = CreateDistributor.objects.get(email=email)
        except CreateDistributor.DoesNotExist:
            return Response({"error": "Distributor not found,Please Contect Admin Team"}, status=status.HTTP_404_NOT_FOUND)

        otp=str(random.randint(100000, 999999))
        distributor.otp = otp
        distributor.otp_created_at = timezone.now()
        distributor.save()
        try:
            send_otp_email(distributor.email,otp, shop_name=distributor.Shop_name)
            print(f"📱📱📱📱OTP for {distributor.Shop_name}: {otp} (to {email})")
            
        except Exception as e:
            return Response({"error": f"Failed to send OTP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
           
# ===============================
# Distributor Verify OTP
# ===============================

# {
#   "email": "example@gmail.com",
#   "otp": "123456"
# }

class DistributorVerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        if not email or not otp:
            return Response({"error": "Email and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            distributor = CreateDistributor.objects.get(email=email)
        except CreateDistributor.DoesNotExist:
            return Response({"error": "Invalid Email or OTP"}, status=status.HTTP_404_NOT_FOUND)

        # check otp presence
        if not distributor.otp or not distributor.otp_created_at:
            return Response({"error": "No OTP has been sent. Request OTP first."}, status=status.HTTP_400_BAD_REQUEST)

        # # check OTP expiry
        # if distributor.otp != str(otp) or timezone.now() - distributor.otp_created_at > timedelta(minutes=OTP_VALIDITY_MINUTES):
        #     return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # Create tokens and include distributor id
        tokens = get_tokens_for_identity(distributor.Company_id, "distributor", distributor_id=distributor.Company_id)
        return Response({
            "message": "Login successful",
            "Shop_name": distributor.Shop_name,
            "email": distributor.email,
            "tokens": tokens
        }, status=status.HTTP_200_OK)
        
            
# -------------------------------------------------------------------
# 🔹 Distributor profile management (/me)
# -------------------------------------------------------------------

class DistributorMeView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    
    def get(self,request):
        token=request.auth
        if not token or token.get('user_type')!='distributor':
            return Response({"error":"Sorry you are Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        distributor=get_object_or_404(CreateDistributor,Company_id=token['user_id'])
        data=DistributorSerializer(distributor, context={'request': request}).data
        return Response(data)
    
def patch(self, request):
    token = request.auth
    if not token or token.get('user_type') != 'distributor':
        return Response({"error": "Sorry you are Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

    distributor = get_object_or_404(CreateDistributor, Company_id=token['user_id'])
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
        email = request.data.get("Email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=400)

        try:
            user = CreateSubUser.objects.get(Email=email)
        except CreateSubUser.DoesNotExist:
            return Response({"error": "Invalid Email"}, status=404)

        if user.check_password(password):
            tokens = get_tokens_for_identity(user.id, "subuser", distributor_id=user.distributor.Company_id if user.distributor else None)
            
            return Response({
                "message": "Login successful",
                "Shop_Name": user.Shop_Name,
                "Email": user.Email,
                "tokens": tokens
            }, status=200)
        else:
            return Response({"error": "Incorrect password"}, status=400)



