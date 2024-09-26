from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.utils import timezone
from ..models import Asset, Transaction
from decimal import Decimal

class PortfolioService:
    @staticmethod
    def add_transaction(portfolio, asset_symbol, transaction_type, quantity, price, timestamp=None):
        quantity = Decimal(str(quantity))
        price = Decimal(str(price))

        if quantity <= Decimal('0'):
            raise ValidationError("Transaction quantity must be greater than zero")
        if price <= Decimal('0'):
            raise ValidationError("Transaction price must be greater than zero")

        with db_transaction.atomic():
            # Check if the asset exists in the user's portfolio
            asset = Asset.objects.filter(portfolio=portfolio, symbol=asset_symbol).first()

            if transaction_type == 'sell':
                if not asset:
                    raise ValidationError("Cannot sell an asset that is not in the portfolio")
                if asset.quantity < quantity:
                    raise ValidationError("Insufficient asset quantity for sale")
                # Proceed with the sell transaction
                asset.quantity -= quantity
                asset.current_price = price  # Update the current price
                asset.save()
            elif transaction_type == 'buy':
                if not asset:
                    # Asset doesn't exist, fetch info from external API and create new asset
                    asset_info = PortfolioService.fetch_asset_info(asset_symbol)
                    asset = Asset.objects.create(
                        portfolio=portfolio,
                        symbol=asset_symbol,
                        name=asset_info['name'],
                        asset_type=asset_info['asset_type'],
                        quantity=quantity,
                        current_price=price
                    )
                else:
                    # Asset exists, update quantity
                    asset.quantity += quantity
                    asset.current_price = price  # Update the current price
                    asset.save()
            else:
                raise ValidationError("Invalid transaction type")

            # Create the transaction
            transaction = Transaction.objects.create(
                portfolio=portfolio,
                asset_symbol=asset_symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                price=price,
                timestamp=timestamp or timezone.now()
            )

        return transaction, asset

    @staticmethod
    def fetch_asset_info(asset_symbol):
        # TODO: Implement external API call to fetch asset info
        # This is a placeholder implementation
        return {
            'name': f"Asset {asset_symbol}",
            'asset_type': 'stock',  # Default to stock, adjust as needed
        }