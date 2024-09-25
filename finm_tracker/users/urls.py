from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserViewSet.as_view({'post': 'register'}), name='user-register'),
    path('me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
]