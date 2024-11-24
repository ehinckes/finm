from rest_framework import serializers
from .models import Portfolio, Asset, Transaction
from users.serializers import UserSerializer

class AssetSerializer(serializers.ModelSerializer):
    """
    Serializer for Asset model.
    Includes calculated fields for financial metrics.
    """
    # Read-only calculated fields from model properties
    total_cost = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    average_cost = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    market_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    profit_loss = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Asset
        fields = [
            'id',
            'symbol',
            'name',
            'asset_type',
            'position',
            'last_price',
            'market_value',
            'profit_loss',
            'total_cost',
            'average_cost',
            'sector'
        ]
        # Protect calculated and system fields from direct modification
        read_only_fields = [
            'id',
            'average_cost',
            'total_cost',
            'market_value',
            'profit_loss'
        ]

    def to_representation(self, instance):
        """
        Convert asset_type from code to display name in API response.
        Example: 'stock_us' becomes 'US Stock'
        """
        representation = super().to_representation(instance)
        representation['asset_type'] = instance.get_asset_type_display()
        return representation


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Transaction model.
    Includes calculated transaction value.
    """
    # Read-only calculated field from model property
    transaction_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            'id',
            'asset_symbol',
            'transaction_type',
            'quantity',
            'price',
            'timestamp',
            'transaction_value'
        ]
        # Protect system-generated and calculated fields
        read_only_fields = [
            'id',
            'timestamp',
            'transaction_value'
        ]


class PortfolioSerializer(serializers.ModelSerializer):
    """
    Serializer for Portfolio model.
    Includes nested serializers for related assets and transactions.
    """
    # Nested serializers for related models
    assets = AssetSerializer(
        many=True,
        read_only=True
    )
    transactions = TransactionSerializer(
        many=True,
        read_only=True
    )
    user = UserSerializer(
        read_only=True
    )
    
    # Read-only calculated fields from model properties
    assets_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    assets_cost = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Portfolio
        fields = [
            'id',
            'user',
            'assets',
            'transactions',
            'assets_value',
            'assets_cost'
        ]
        read_only_fields = [
            'id',
            'assets_value',
            'assets_cost'
        ]