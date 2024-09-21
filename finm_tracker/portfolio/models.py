from django.db import models
from django.contrib.auth.models import User

class Asset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    asset_type = models.CharField(max_length=50)  # e.g., 'stock', 'crypto', 'bond'

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10)  # 'buy' or 'sell'
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)