from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

class Portfolio(models.Model):
    """
    Portfolio model representing a user's collection of assets and transactions.
    Each user can have only one portfolio (OneToOneField).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        """String representation of the portfolio"""
        return f"{self.user.username}'s Portfolio"

    @property
    def assets_value(self):
        """
        Calculate total current market value of all assets in portfolio.
        Returns: Decimal representing total portfolio value
        """
        return sum(asset.market_value for asset in self.assets.all())

    @property
    def assets_cost(self):
        """
        Calculate total cost basis of all assets in portfolio.
        Returns: Decimal representing total cost of all assets
        """
        return sum(asset.total_cost for asset in self.assets.all())

class Asset(models.Model):
    """
    Asset model representing a single holding in a portfolio.
    Can be a US stock, Australian stock, or cryptocurrency.
    """
    ASSET_TYPES = [
        ('stock_us', 'US Stock'),
        ('stock_au', 'AUS Stock'),
        ('crypto', 'Cryptocurrency'),
    ]

    portfolio = models.ForeignKey(
        Portfolio,
        related_name='assets',
        on_delete=models.CASCADE
    )
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=10, choices=ASSET_TYPES)
    position = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=0
    )  # Current quantity held
    last_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )  # Most recent market price
    sector = models.CharField(max_length=100)  # Industry sector

    class Meta:
        unique_together = ['portfolio', 'symbol']  # Prevent duplicate assets

    def __str__(self):
        """String representation of the asset"""
        return f"{self.symbol} - {self.name} ({self.position})"

    def clean(self):
        """
        Validate asset data:
        - Position cannot be negative
        - Price cannot be negative
        """
        if self.position < 0:
            raise ValidationError("Asset quantity cannot be negative.")
        if self.last_price < 0:
            raise ValidationError("Asset price cannot be negative.")

    @property
    def market_value(self):
        """
        Calculate current market value of the asset.
        Returns: Decimal of position * last_price, or 0 if price is unknown
        """
        if self.last_price is not None:
            return self.position * self.last_price
        return Decimal('0.00')

    @property
    def total_cost(self):
        """
        Calculate total cost basis of the asset:
        Total of buy transactions minus total of sell transactions
        """
        buy_transactions_cost = sum(
            transaction.transaction_value 
            for transaction in self.portfolio.transactions.filter(
                asset_symbol=self.symbol,
                transaction_type='buy'
            )
        )
        sell_transactions_value = sum(
            transaction.transaction_value 
            for transaction in self.portfolio.transactions.filter(
                asset_symbol=self.symbol,
                transaction_type='sell'
            )
        )
        return buy_transactions_cost - sell_transactions_value

    @property
    def average_cost(self):
        """
        Calculate average cost per unit of the asset.
        Returns: Decimal of total_cost / position, or 0 if no position
        """
        return self.total_cost / self.position if self.position > 0 else Decimal('0.00')

    @property
    def profit_loss(self):
        """
        Calculate unrealized profit/loss.
        Returns: Decimal of market_value - total_cost
        """
        return self.market_value - self.total_cost

class Transaction(models.Model):
    """
    Transaction model representing buys and sells of assets.
    Each transaction is tied to a portfolio and has a unique timestamp.
    """
    TRANSACTION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    portfolio = models.ForeignKey(
        Portfolio,
        related_name='transactions',
        on_delete=models.CASCADE
    )
    asset_symbol = models.CharField(max_length=10)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=15, decimal_places=6)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['portfolio', 'timestamp']  # Ensure unique timestamps

    def __str__(self):
        """String representation of the transaction"""
        return f"{self.transaction_type} {self.quantity} {self.asset_symbol} at {self.price}"

    def clean(self):
        """
        Validate transaction data:
        - Quantity cannot be negative
        - Price cannot be negative
        """
        if self.quantity < 0:
            raise ValidationError("Transaction quantity cannot be negative.")
        if self.price < 0:
            raise ValidationError("Transaction price cannot be negative.")

    @property
    def transaction_value(self):
        """
        Calculate total value of the transaction.
        Returns: Decimal of quantity * price
        """
        return self.quantity * self.price

    @property
    def weight_and_time(self):
        """
        Calculate the weight and time for buy transactions.
        Used for time-weighted calculations.
        Returns: Tuple of (quantity, years_elapsed) for buys, None for sells
        """
        if self.transaction_type == 'buy':
            time_elapsed = timezone.now() - self.timestamp
            return self.quantity, time_elapsed.total_seconds()/31536000  # Convert to years
        return None