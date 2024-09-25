from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PortfolioViewSet, AssetViewSet, TransactionViewSet,
    home_view, register_view, login_view, logout_view, assets_view, transactions_view, add_transaction_view
)

router = DefaultRouter()
router.register(r'portfolios', PortfolioViewSet, basename='portfolio')
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'transactions', TransactionViewSet, basename='transaction')

# API routes
api_urlpatterns = [
    path('api/', include(router.urls)),
]

# Web routes
web_urlpatterns = [
    path('', home_view, name='home'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('assets/', assets_view, name='assets'),
    path('transactions/', transactions_view, name='transactions'),
    path('add-transaction/', add_transaction_view, name='add_transaction'),
]

# Combine all routes
urlpatterns = api_urlpatterns + web_urlpatterns