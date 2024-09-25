from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

class Portfolio(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.user.username}'s Portfolio"


class Asset(models.Model):
    ASSET_TYPES = [
        ('stock', 'Stock'),
        ('crypto', 'Cryptocurrency'),
        ('commodity', 'Commodity'),
        ('forex', 'Forex'),
        ('bond', 'Bond'),
    ]

    portfolio = models.ForeignKey(Portfolio, related_name='assets', on_delete=models.CASCADE)
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    quantity = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    current_price = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        unique_together = ['portfolio', 'symbol']

    def __str__(self):
        return f"{self.symbol} - {self.name} ({self.quantity})"

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Asset quantity cannot be negative.")
        if self.current_price < 0:
            raise ValidationError("Asset price cannot be negative.")


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    portfolio = models.ForeignKey(Portfolio, related_name='transactions', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    asset_symbol = models.CharField(max_length=10)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=15, decimal_places=6)
    price = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        unique_together = ['portfolio', 'timestamp']

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.asset_symbol} at {self.price}"

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Transaction quantity cannot be negative.")
        if self.price < 0:
            raise ValidationError("Transaction price cannot be negative.")
