from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

class Portfolio(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.user.username}'s Portfolio"
    
    @property
    def assets_value(self):
        return sum(asset.current_value for asset in self.assets.all())

    @property
    def assets_cost(self):
        buy_transactions = self.transactions.filter(transaction_type='buy')
        sell_transactions = self.transactions.filter(transaction_type='sell')
        
        total_buy = sum(transaction.current_value for transaction in buy_transactions)
        total_sell = sum(transaction.current_value for transaction in sell_transactions)
        
        return total_buy - total_sell


class Asset(models.Model):
    ASSET_TYPES = [
        ('stock_us', 'US Stock'),
        ('stock_au', 'Aus Stock'),
        ('crypto', 'Cryptocurrency'),
    ]

    portfolio = models.ForeignKey(Portfolio, related_name='assets', on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    quantity = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    current_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ['portfolio', 'symbol']

    def __str__(self):
        return f"{self.symbol} - {self.name} ({self.quantity})"

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Asset quantity cannot be negative.")
        if self.current_price < 0:
            raise ValidationError("Asset price cannot be negative.")
        
    @property
    def current_value(self):
        if self.current_price is not None:
            return self.quantity * self.current_price
        return Decimal('0.00')
    
    @property
    def profit_loss(self):
        buy_transactions_cost = sum(
            transaction.current_value for transaction in self.portfolio.transactions.filter(
                asset_symbol=self.symbol, transaction_type='buy'
            )
        )
        sell_transactions_value = sum(
            transaction.current_value for transaction in self.portfolio.transactions.filter(
                asset_symbol=self.symbol, transaction_type='sell'
            )
        )
        return self.current_value - (buy_transactions_cost - sell_transactions_value)



class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    portfolio = models.ForeignKey(Portfolio, related_name='transactions', on_delete=models.CASCADE)
    asset_symbol = models.CharField(max_length=10)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=15, decimal_places=6)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['portfolio', 'timestamp']

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.asset_symbol} at {self.price}"

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Transaction quantity cannot be negative.")
        if self.price < 0:
            raise ValidationError("Transaction price cannot be negative.")
        
    @property
    def current_value(self):
        return self.quantity * self.price
