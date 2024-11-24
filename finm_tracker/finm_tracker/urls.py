from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views as auth_views

# URL configuration for the entire finm_tracker project
urlpatterns = [
    # Django admin interface URL
    path('admin/', admin.site.urls),
    
    # User management URLs (authentication, registration, profile management)
    path('users/', include('users.urls')),
    
    # Main application URLs - portfolio management and tracking functionality
    # Using '' as prefix means these URLs will be at the root level
    path('', include('portfolio.urls')),
    
    # Django REST framework authentication URLs
    # Provides login/logout views for the browsable API
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # Token authentication endpoint for API access
    # Used to obtain authentication tokens for API requests
    path('api-token-auth/', auth_views.obtain_auth_token),
]