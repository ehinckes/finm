from django.contrib import admin
from .models import Portfolio, Asset, Transaction

# Inline Admin for Assets - allows editing assets directly in Portfolio admin
class AssetInline(admin.TabularInline):
    model = Asset
    extra = 1  # Number of empty forms to display for adding new assets

# Inline Admin for Transactions - allows editing transactions directly in Portfolio admin
class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 1  # Number of empty forms to display for adding new transactions

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    """
    Admin configuration for Portfolio model.
    Shows user and calculated totals in list view.
    Includes inline editing for related Assets and Transactions.
    """
    list_display = ('user', 'get_total_assets', 'get_total_transactions')
    inlines = [AssetInline, TransactionInline]

    def get_total_assets(self, obj):
        """Calculate and return the total number of assets in the portfolio"""
        return obj.assets.count()
    get_total_assets.short_description = 'Total Assets'

    def get_total_transactions(self, obj):
        """Calculate and return the total number of transactions in the portfolio"""
        return obj.transactions.count()
    get_total_transactions.short_description = 'Total Transactions'

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """
    Admin configuration for Asset model.
    Displays comprehensive asset information in list view.
    Provides filtering by asset type and portfolio.
    Enables searching by symbol and name.
    """
    list_display = ('symbol', 'name', 'asset_type', 'position', 'last_price', 'portfolio')
    list_filter = ('asset_type', 'portfolio')  # Filters in the right sidebar
    search_fields = ('symbol', 'name')  # Fields used in admin search

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Transaction model.
    Shows transaction details in list view.
    Provides filtering by transaction type and portfolio.
    Enables searching by asset symbol.
    """
    list_display = ('portfolio', 'timestamp', 'asset_symbol', 'transaction_type', 
                   'quantity', 'price')
    list_filter = ('transaction_type', 'portfolio')  # Filters in the right sidebar
    search_fields = ('asset_symbol',)  # Fields used in admin search