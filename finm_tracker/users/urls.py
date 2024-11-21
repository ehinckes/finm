from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Initialize DRF router for RESTful endpoints
router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    # Include all auto-generated router URLs
    path('', include(router.urls)),
    
    # Custom endpoints for specific user operations
    path('register/', UserViewSet.as_view({'post': 'register'}), name='user-register'),
    path('me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
]