from django.contrib import admin
from .models import Portfolio, Asset, Transaction

class AssetInline(admin.TabularInline):
    model = Asset
    extra = 1

class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 1

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_total_assets', 'get_total_transactions')
    inlines = [AssetInline, TransactionInline]

    def get_total_assets(self, obj):
        return obj.assets.count()
    get_total_assets.short_description = 'Total Assets'

    def get_total_transactions(self, obj):
        return obj.transactions.count()
    get_total_transactions.short_description = 'Total Transactions'

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'asset_type', 'quantity', 'current_price', 'portfolio')
    list_filter = ('asset_type', 'portfolio')
    search_fields = ('symbol', 'name')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'timestamp', 'asset_symbol', 'transaction_type', 'quantity', 'price')
    list_filter = ('transaction_type', 'portfolio')
    search_fields = ('asset_symbol',)