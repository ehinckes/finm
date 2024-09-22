from rest_framework import serializers
from .models import Asset, Transaction

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['id', 'name', 'symbol', 'asset_type', 'quantity', 'user']
        read_only_fields = ['user']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'asset', 'transaction_type', 'quantity', 'price', 'date', 'user']
        read_only_fields = ['date', 'user']
