from django.urls import path
from . import views

urlpatterns = [
    path('portfolio/', views.portfolio_detail, name='portfolio-detail'),
    path('assets/', views.asset_list, name='asset-list'),
    path('assets/<int:pk>/', views.asset_detail, name='asset-detail'),
    path('transactions/', views.transaction_list, name='transaction-list'),
    path('transactions/<int:pk>/', views.transaction_detail, name='transaction-detail'),
]