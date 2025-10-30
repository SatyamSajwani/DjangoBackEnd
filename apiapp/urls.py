from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from apiapp.views import *
from rest_framework import routers

# Initialize the DRF router
router = routers.DefaultRouter()

# 🛞 Products (Tyre Models)
# Handles all CRUD (GET, POST, PUT, DELETE) for tyre products
# Example: /api/v1/products/
router.register(r'products', CreateTyreModelViewSet, basename='products')

# 🧩 Tyre Patterns
# Each tyre pattern belongs to a tyre model
# Example: /api/v1/patterns/
router.register(r'patterns', TyrePatternViewSet, basename='patterns')

# 🏷️ Brands
# Manage tyre brands (e.g., MRF, CEAT, Apollo)
# Example: /api/v1/brands/
router.register(r'brands', BrandViewSet, basename='brands')

# 🧍‍♂️ Distributors
# Main accounts that can log in using OTP
# Example: /api/v1/distributors/
router.register(r'distributors', CreatedistributorViewSet, basename='distributors')

# 👥 Subusers under each distributor
# Nested route — shows or creates subusers for a specific distributor
# Example: /api/v1/distributors/2/subusers/
router.register(r'distributors/(?P<distributor_pk>[^/.]+)/subusers', DistributorSubUserViewSet, basename='distributor-subusers')


# 📜 Custom URLs (not part of router)
urlpatterns = [
    # 📱 Distributor OTP Request
    # Step 1: Distributor enters email or mobile → system sends OTP
    # Method: POST
    # Example: /api/v1/distributor/request-otp/
    path('distributor/request-otp/', DistributorSendOTPView.as_view(), name='distributor_request_otp'),

    # ✅ Verify OTP and Login
    # Step 2: Distributor enters OTP → system verifies and returns JWT tokens
    # Method: POST
    # Example: /api/v1/distributor/verify-otp/
    path('distributor/verify-otp/', DistributorVerifyOTPView.as_view(), name='distributor_verify_otp'),

    # 👤 Fetch Distributor Profile
    # Used to get the logged-in distributor’s own info (via access token)
    # Method: GET
    # Example: /api/v1/distributor/me/
    path('distributor/me/', DistributorMeView.as_view(), name='distributor_me'),

    # 🔐 Subuser Login
    # Allows a subuser to log in using username/password or OTP (based on your logic)
    # Method: POST
    # Example: /api/v1/subuser/login/
    path('subuser/login/', SubUserLoginView.as_view(), name='subuser_login'),

    # 🧭 Include all router-based endpoints (products, brands, etc.)
    path('', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
