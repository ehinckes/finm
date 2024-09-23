from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class Portfolio(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username}'s Portfolio"


class Asset(models.Model):
    ASSET_TYPES = [
        ('STOCK', 'Stock'),
        ('CRYPTO', 'Cryptocurrency'),
        ('COMMODITY', 'Commodity'),
        ('FOREX', 'Forex'),
        ('BOND', 'Bond'),
    ]

    portfolio = models.ForeignKey(Portfolio, related_name='assets', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    portfolio = models.ForeignKey(Portfolio, related_name='transactions', on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.quantity:.2f} {self.asset.symbol} at {self.price:.2f}"

    def save(self, *args, **kwargs):
        if self.transaction_type == 'SELL' and self.quantity > self.asset.quantity:
            raise ValueError("Cannot sell more than owned quantity")
        super().save(*args, **kwargs)
        self.update_asset_quantity()

    def update_asset_quantity(self):
        if self.transaction_type == 'BUY':
            self.asset.quantity += self.quantity
        elif self.transaction_type == 'SELL':
            self.asset.quantity -= self.quantity
        self.asset.save()


# When new user is created, create a Portfolio for them
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_portfolio(sender, instance, created, **kwargs):
    if created:
        Portfolio.objects.create(user=instance)

# When user is saved, save their Portfolio
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_portfolio(sender, instance, **kwargs):
    instance.portfolio.save()