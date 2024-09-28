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
    @staticmethod
    def add_transaction(portfolio, asset_symbol, asset_type, transaction_type, quantity, price, timestamp):
        quantity = Decimal(str(quantity))
        price = Decimal(str(price))

        if quantity <= Decimal('0'):
            raise ValidationError("Transaction quantity must be greater than zero")
        if price <= Decimal('0'):
            raise ValidationError("Transaction price must be greater than zero")
        if timestamp > timezone.now():
            raise ValidationError("Transaction timestamp cannot be in the future")
        
        if asset_type == 'stock_us':
            pass
        elif asset_type == 'stock_au':
            if not asset_symbol.endswith(".AX"):
                asset_symbol += ".AX"
        elif asset_type == 'crypto':
            if not asset_symbol.endswith("-USD"):
                asset_symbol += "-USD"
        else:
            raise ValueError("Invalid asset type")

        with db_transaction.atomic():
            
            # Check if the asset exists in the user's portfolio
            asset = Asset.objects.filter(portfolio=portfolio, symbol=asset_symbol).first()
            if asset:
                if transaction_type == 'sell':
                    if asset.position < quantity:
                        raise ValidationError("Insufficient asset quantity for sale")
                    # Proceed with the sell transaction
                    asset.position -= quantity
                    asset.save()
                elif transaction_type == 'buy':
                    # Proceed with buy transaction
                    asset.position += quantity
                    asset.save()
                else:
                    raise ValidationError("Invalid transaction type")

            elif not asset:
                if transaction_type == 'sell':
                    raise ValidationError("Cannot sell an asset that is not in the portfolio")
                

                elif transaction_type == 'buy':
                    # Asset doesn't exist, fetch info from external API and create new asset
                    asset_info = ExternalAPIService.fetch_asset_info(asset_symbol, asset_type)
                    asset = Asset.objects.create(
                        portfolio=portfolio,
                        symbol=asset_symbol,
                        name=asset_info['name'],
                        asset_type=asset_type,
                        position=quantity,
                        last_price=asset_info['last_price']
                    )

                else:
                    raise ValidationError("Invalid transaction type")
                    

            # Create the transaction
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
        # Try to get the data from cache first
        cache_key = 'daily_movers'
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return cached_data
        
         # If not in cache, fetch the data
        movers = []
        movers.append(CustomScrapingService.fetch_stock_movers("gainers"))
        movers.append(CustomScrapingService.fetch_stock_movers("losers"))
        movers.append(CustomScrapingService.fetch_crypto_movers("gainers"))
        movers.append(CustomScrapingService.fetch_crypto_movers("losers"))

        # Cache the data for 15 minutes (adjust as needed)
        cache.set(cache_key, movers, 60 * 15)

        return movers