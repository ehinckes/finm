from django.contrib import admin
from .models import Portfolio, Asset, Transaction

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('user',)

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'asset_type', 'quantity', 'current_price', 'portfolio')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('asset', 'transaction_type', 'quantity', 'price', 'date', 'portfolio')