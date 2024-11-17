from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.utils import timezone
from ..models import Asset, Transaction
from decimal import Decimal
from .external_api_service import ExternalAPIService
from .custom_scraping_services import CustomScrapingService
from django.core.cache import cache
from django.conf import settings

class PortfolioService:
    """
    Orchestrator service that manages portfolio operations by coordinating between
    models, external APIs, and web scraping services. Handles transaction processing
    and market data retrieval with proper validation and error handling.
    """

    @staticmethod
    def add_transaction(portfolio, asset_symbol, asset_type, transaction_type, quantity, price, timestamp):
        """
        Processes a buy/sell transaction and updates portfolio accordingly.
        Uses database transaction to ensure data consistency.
        
        Args:
            portfolio: Portfolio model instance
            asset_symbol (str): Trading symbol of the asset
            asset_type (str): Type of asset ('stock_us', 'stock_au', 'crypto')
            transaction_type (str): Type of transaction ('buy' or 'sell')
            quantity (Decimal/str/float): Amount of asset to buy/sell
            price (Decimal/str/float): Price per unit of the asset
            timestamp: DateTime of the transaction
            
        Returns:
            tuple: (Transaction instance, Asset instance)
            
        Raises:
            ValidationError: For invalid quantities, prices, or insufficient holdings
        """
        # Convert inputs to Decimal for precise calculations
        quantity = Decimal(str(quantity))
        price = Decimal(str(price))

        # Validate transaction parameters
        if quantity <= Decimal('0'):
            raise ValidationError("Transaction quantity must be greater than zero")
        if price <= Decimal('0'):
            raise ValidationError("Transaction price must be greater than zero")
        if timestamp > timezone.now():
            raise ValidationError("Transaction timestamp cannot be in the future")
        
        # Standardize asset symbols based on type
        if asset_type == 'stock_us':
            pass  # US stocks need no modification
        elif asset_type == 'stock_au':
            if not asset_symbol.endswith(".AX"):
                asset_symbol += ".AX"  # Add ASX suffix if missing
        elif asset_type == 'crypto':
            if not asset_symbol.endswith("-USD"):
                asset_symbol += "-USD"  # Add USD pair suffix if missing
        else:
            raise ValueError("Invalid asset type")

        # Use database transaction to ensure atomicity
        with db_transaction.atomic():
            
            # Check if asset exists in portfolio
            asset = Asset.objects.filter(portfolio=portfolio, symbol=asset_symbol).first()
            
            if asset:
                # Handle existing asset
                if transaction_type == 'sell':
                    if asset.position < quantity:
                        raise ValidationError("Insufficient asset quantity for sale")
                    asset.position -= quantity
                    asset.save()
                elif transaction_type == 'buy':
                    asset.position += quantity
                    asset.save()
                else:
                    raise ValidationError("Invalid transaction type")

            else:
                # Handle new asset
                if transaction_type == 'sell':
                    raise ValidationError("Cannot sell an asset that is not in the portfolio")
                elif transaction_type == 'buy':
                    # Fetch asset info from external API for new assets
                    asset_info = ExternalAPIService.fetch_asset_info(asset_symbol, asset_type)
                    asset = Asset.objects.create(
                        portfolio=portfolio,
                        symbol=asset_symbol,
                        name=asset_info['name'],
                        asset_type=asset_type,
                        position=quantity,
                        last_price=asset_info['last_price'],
                        sector=asset_info['sector']
                    )
                else:
                    raise ValidationError("Invalid transaction type")

            # Record the transaction
            transaction = Transaction.objects.create(
                portfolio=portfolio,
                asset_symbol=asset_symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                price=price,
                timestamp=timestamp,
            )

        return transaction, asset
    
    @staticmethod
    def fetch_daily_gainers():
        """
        Retrieves daily market movers (gainers and losers) for both stocks and crypto.
        Implements caching to reduce API calls and improve performance.
        
        Returns:
            list: List containing four sublists:
                 [stock_gainers, stock_losers, crypto_gainers, crypto_losers]
        """
        # Check cache first
        cache_key = 'daily_movers'
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return cached_data
        
        # If not in cache, fetch fresh data
        movers = []
        movers.append(CustomScrapingService.fetch_stock_movers("gainers"))
        movers.append(CustomScrapingService.fetch_stock_movers("losers"))
        movers.append(CustomScrapingService.fetch_crypto_movers("gainers"))
        movers.append(CustomScrapingService.fetch_crypto_movers("losers"))

        # Cache results for 15 minutes
        cache.set(cache_key, movers, 60 * 15)

        return movers

    @staticmethod
    def update_portfolio_prices(portfolio):
        """
        Updates the last_price for all assets in a portfolio.
        Uses caching to prevent too frequent updates.
        
        Args:
            portfolio: Portfolio model instance
            
        Returns:
            dict: Summary of update results
            {
                'updated': number of prices updated,
                'failed': number of failed updates,
                'cached': boolean indicating if cached data was used
            }
        """
        # Check cache first
        cache_key = f'portfolio_prices_{portfolio.id}'
        if cache.get(cache_key):
            return {'updated': 0, 'failed': 0, 'cached': True}

        assets = portfolio.assets.all()
        updated = 0
        failed = 0

        for asset in assets:
            # Format symbol if needed
            symbol = asset.symbol
            if asset.asset_type == 'stock_au' and not symbol.endswith('.AX'):
                symbol += '.AX'
            elif asset.asset_type == 'crypto' and not symbol.endswith('-USD'):
                symbol += '-USD'

            # Fetch new price
            new_price = ExternalAPIService.fetch_latest_price(symbol, asset.asset_type)
            
            if new_price is not None:
                asset.last_price = new_price
                asset.save()
                updated += 1
            else:
                failed += 1

        # Cache the update timestamp for 15 minutes
        cache.set(cache_key, True, 60 * 15)  # 15 minutes

        return {
            'updated': updated,
            'failed': failed,
            'cached': False
        }

    @staticmethod
    def get_portfolio_with_fresh_prices(portfolio):
        """
        Convenience method that returns a portfolio with updated prices.
        This is useful for views that need to display current portfolio value.
        
        Args:
            portfolio: Portfolio model instance
            
        Returns:
            tuple: (Portfolio instance, Update summary dict)
        """
        update_summary = PortfolioService.update_portfolio_prices(portfolio)
        return portfolio, update_summary
