from rest_framework import serializers
from .models import Portfolio, Asset, Transaction
from users.serializers import UserSerializer

class AssetSerializer(serializers.ModelSerializer):
    cost_of_goods= serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    market_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    profit_loss = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Asset
        fields = ['id', 'symbol', 'name', 'asset_type', 'quantity', 'last_price', 'market_value', 'profit_loss', 'cost_of_goods']
        read_only_fields = ['id', 'cost_price', 'value', 'profit_loss']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['asset_type'] = instance.get_asset_type_display()
        return representation

class TransactionSerializer(serializers.ModelSerializer):
    transaction_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'asset_symbol', 'transaction_type', 'quantity', 'price', 'timestamp', 'transaction_value']
        read_only_fields = ['id', 'timestamp', 'value']

class PortfolioSerializer(serializers.ModelSerializer):
    assets = AssetSerializer(many=True, read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    assets_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    assets_cost = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Portfolio
        fields = ['id', 'user', 'assets', 'transactions', 'assets_value', 'assets_cost']
        read_only_fields = ['id', 'assets_value', 'assets_cost']