from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PortfolioViewSet, AssetViewSet, TransactionViewSet,
    home_view, register_view, login_view, logout_view, 
    assets_view, transactions_view, add_transaction_view, 
    performance_view, risks_view, projections_view, 
    export_transactions_csv
)

# Initialize the DRF router for automatic URL routing for ViewSets
router = DefaultRouter()

# Register ViewSets with the router
# Each registration creates multiple URL patterns for different actions (list, detail, etc.)
router.register(r'portfolios', PortfolioViewSet, basename='portfolio')
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'transactions', TransactionViewSet, basename='transaction')

# API routes - RESTful endpoints for programmatic access
api_urlpatterns = [
    # Include all routes generated by the DRF router
    path('api/', include(router.urls)),
]

# Web routes - Traditional web views for browser access
web_urlpatterns = [
    # Authentication and main views
    path('', home_view, name='home'),                    # Landing page
    path('register/', register_view, name='register'),   # User registration
    path('login/', login_view, name='login'),           # User login
    path('logout/', logout_view, name='logout'),        # User logout
    
    # Portfolio management views
    path('assets/', assets_view, name='assets'),        # View all assets
    path('transactions/', transactions_view, name='transactions'),  # View all transactions
    path('add-transaction/', add_transaction_view, name='add_transaction'),  # Add new transaction
    
    # Analysis and reporting views
    path('performance/', performance_view, name='performance'),  # Portfolio performance analysis
    path('risks/', risks_view, name='risks'),                   # Risk assessment
    path('projections/', projections_view, name='projections'), # Future projections
    
    # Data export functionality
    path('export-transactions/', export_transactions_csv, name='export_transactions'),  # Export transactions as CSV
]

# Combine API and web routes into a single URL patterns list
urlpatterns = api_urlpatterns + web_urlpatterns