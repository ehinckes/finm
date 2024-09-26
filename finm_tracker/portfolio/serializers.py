from rest_framework import serializers
from .models import Portfolio, Asset, Transaction
from users.serializers import UserSerializer

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['id', 'symbol', 'name', 'asset_type', 'quantity', 'current_price']
        read_only_fields = ['id']

        def to_representation(self, instance):
            representation = super().to_representation(instance)
            representation['asset_type'] = instance.get_asset_type_display()
            return representation

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'asset_symbol', 'transaction_type', 'quantity', 'price', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class PortfolioSerializer(serializers.ModelSerializer):
    assets = AssetSerializer(many=True, read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Portfolio
        fields = ['id', 'user', 'assets', 'transactions']
        read_only_fields = ['id']