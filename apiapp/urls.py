from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

# Import ViewSets and Views
from apiapp.views import *

# Correct router imports
from rest_framework import routers as drf_routers           # DefaultRouter
from rest_framework_nested import routers as nested_routers # NestedRouter


# -------------------------------------------------------------------
# 🔵 MAIN ROUTER (DEFAULT DRF ROUTER)
# -------------------------------------------------------------------
router = drf_routers.DefaultRouter()

# 🛞 PRODUCTS (Tyre Models CRUD)
# Endpoint:
#   GET    /api/v1/products/
#   POST   /api/v1/products/
#   PUT    /api/v1/products/<id>/
#   DELETE /api/v1/products/<id>/
router.register(r'products', CreateTyreModelViewSet, basename='products')

# 🧩 PATTERNS (Under Tyre Models)
# Endpoint:
#   GET  /api/v1/patterns/
router.register(r'patterns', TyrePatternViewSet, basename='patterns')

# 🏷️ BRANDS
# Endpoint:
#   GET  /api/v1/brands/
#   POST /api/v1/brands/
router.register(r'brands', BrandViewSet, basename='brands')

# 🧍‍♂️ DISTRIBUTORS (Main Accounts)
# Endpoint:
#   GET  /api/v1/distributors/
#   POST /api/v1/distributors/
router.register(r'distributors', CreatedistributorViewSet, basename='distributors')


# -------------------------------------------------------------------
# 🔵 NESTED ROUTES FOR SUBUSERS
# -------------------------------------------------------------------
# A subuser belongs to a specific distributor
# Final Endpoints:
#   GET  /api/v1/distributors/<id>/subusers/
#   POST /api/v1/distributors/<id>/subusers/
subuser_router = nested_routers.NestedSimpleRouter(
    router, r'distributors', lookup='distributor'
)

subuser_router.register(
    r'subusers',
    DistributorSubUserViewSet,
    basename='distributor-subusers'
)


# -------------------------------------------------------------------
# 🔵 CUSTOM ROUTES (NOT USING ROUTERS)
# -------------------------------------------------------------------
urlpatterns = [

    # 📱 SEND OTP TO DISTRIBUTOR
    # Endpoint: POST /api/v1/distributor/send-otp/
    path(
        'distributor/send-otp/',
        DistributorSendOTPView.as_view(),
        name='distributor_request_otp'
    ),

    # 🔐 VERIFY OTP (Distributor Login)
    # Endpoint: POST /api/v1/distributor/verify-otp/
    path(
        'distributor/verify-otp/',
        DistributorVerifyOTPView.as_view(),
        name='distributor_verify_otp'
    ),

    # 👤 Get logged-in Distributor Profile
    # Endpoint: GET /api/v1/distributor/me/
    path(
        'distributor/me/',
        DistributorMeView.as_view(),
        name='distributor_me'
    ),

    # 🔐 SUBUSER LOGIN (DIRECT LOGIN API)
    # FINAL ENDPOINT:
    #     POST /api/v1/subuser/login/
    path(
        'subuser/login/',
        SubUserLoginView.as_view(),
        name='subuser_login'
    ),

    # -------------------------------------------------------------------
    # 🔗 INCLUDE ALL ROUTER URLS
    # -------------------------------------------------------------------
    path('', include(router.urls)),          # Adds: products, brands, distributors, patterns
    path('', include(subuser_router.urls)),  # Adds: distributors/<id>/subusers/

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
