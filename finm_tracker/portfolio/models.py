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
        return sum(asset.market_value for asset in self.assets.all())

    @property
    def assets_cost(self):
        return sum(asset.total_cost for asset in self.assets.all())


class Asset(models.Model):
    ASSET_TYPES = [
        ('stock_us', 'US Stock'),
        ('stock_au', 'AUS Stock'),
        ('crypto', 'Cryptocurrency'),
    ]

    portfolio = models.ForeignKey(Portfolio, related_name='assets', on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    position = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    last_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ['portfolio', 'symbol']

    def __str__(self):
        return f"{self.symbol} - {self.name} ({self.position})"

    def clean(self):
        if self.position < 0:
            raise ValidationError("Asset quantity cannot be negative.")
        if self.last_price < 0:
            raise ValidationError("Asset price cannot be negative.")
        
    @property
    def market_value(self):
        if self.last_price is not None:
            return self.position * self.last_price
        return Decimal('0.00')
    
    @property
    def total_cost(self):
        buy_transactions_cost = sum(
            transaction.transaction_value for transaction in self.portfolio.transactions.filter(
                asset_symbol=self.symbol, transaction_type='buy'
            )
        )
        sell_transactions_value = sum(
            transaction.transaction_value for transaction in self.portfolio.transactions.filter(
                asset_symbol=self.symbol, transaction_type='sell'
            )
        )
        return buy_transactions_cost - sell_transactions_value
    
    @property
    def average_cost(self):
        return self.total_cost / self.position if self.position > 0 else Decimal('0.00')
    
    @property
    def profit_loss(self):
        return self.market_value - self.total_cost



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
    def transaction_value(self):
        return self.quantity * self.price
