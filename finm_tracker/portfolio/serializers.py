from rest_framework import serializers
from .models import Portfolio, Asset, Transaction

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['id', 'name', 'symbol', 'asset_type', 'quantity', 'current_price']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'asset', 'transaction_type', 'quantity', 'price', 'date']

    def validate(self, data):
        if data['transaction_type'] == 'SELL' and data['quantity'] > data['asset'].quantity:
            raise serializers.ValidationError("Cannot sell more than owned quantity")
        return data

class PortfolioSerializer(serializers.ModelSerializer):
    assets = AssetSerializer(many=True, read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Portfolio
        fields = ['id', 'user', 'assets', 'transactions']