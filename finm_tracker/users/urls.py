from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import register_user, user_profile

urlpatterns = [
    path('token/', obtain_auth_token, name='api_token_auth'),
    path('register/', register_user, name='register'),
    path('profile/', user_profile, name='profile'),
]
