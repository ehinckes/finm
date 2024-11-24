from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APITestCase
from ..models import Portfolio, Asset, Transaction
from ..serializers import PortfolioSerializer, AssetSerializer, TransactionSerializer

User = get_user_model()

class AssetSerializerTest(APITestCase):
    """Tests for the Asset serializer focusing on:
    1. Basic field serialization
    2. Calculated financial fields
    3. Read-only field protection
    4. Asset type display conversion
    """
    
    def setUp(self):
        """Create test user and portfolio with sample asset"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.portfolio = self.user.portfolio
        
        self.asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('10.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        # Add transaction for cost basis calculation
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('100.00')
        )

    def test_asset_serialization(self):
        """Test basic asset serialization with all fields"""
        serializer = AssetSerializer(self.asset)
        data = serializer.data
        
        self.assertEqual(data['symbol'], 'AAPL')
        self.assertEqual(data['name'], 'Apple Inc')
        self.assertEqual(data['asset_type'], 'US Stock')
        self.assertEqual(Decimal(data['position']), Decimal('10.0'))
        self.assertEqual(Decimal(data['last_price']), Decimal('150.00'))
        self.assertEqual(data['sector'], 'Technology')

    def test_calculated_fields(self):
        """Test that calculated financial fields are correct"""
        serializer = AssetSerializer(self.asset)
        data = serializer.data
        
        self.assertEqual(Decimal(data['market_value']), Decimal('1500.00'))  # 10 * 150
        self.assertEqual(Decimal(data['total_cost']), Decimal('1000.00'))    # 10 * 100
        self.assertEqual(Decimal(data['average_cost']), Decimal('100.00'))   # 1000 / 10
        self.assertEqual(Decimal(data['profit_loss']), Decimal('500.00'))    # 1500 - 1000

    def test_read_only_fields(self):
        """Test that read-only fields cannot be modified"""
        data = {
            'symbol': 'AAPL',
            'name': 'Apple Inc',
            'asset_type': 'stock_us',
            'position': '10.0',
            'last_price': '150.00',
            'market_value': '9999.99',  # Should be read-only
            'total_cost': '9999.99',    # Should be read-only
            'sector': 'Technology'
        }
        
        serializer = AssetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Verify read-only fields are not included in validated data
        self.assertNotIn('market_value', serializer.validated_data)
        self.assertNotIn('total_cost', serializer.validated_data)

    def test_asset_type_display(self):
        """Test asset type code to display name conversion"""
        assets = [
            Asset.objects.create(
                portfolio=self.portfolio,
                symbol='BTC-USD',
                name='Bitcoin',
                asset_type='crypto',
                position=Decimal('1.0'),
                last_price=Decimal('30000.00'),
                sector='Cryptocurrency'
            ),
            Asset.objects.create(
                portfolio=self.portfolio,
                symbol='BHP.AX',
                name='BHP Group',
                asset_type='stock_au',
                position=Decimal('100.0'),
                last_price=Decimal('40.00'),
                sector='Materials'
            )
        ]
        
        serializer = AssetSerializer(assets, many=True)
        data = serializer.data
        
        self.assertEqual(data[0]['asset_type'], 'Cryptocurrency')
        self.assertEqual(data[1]['asset_type'], 'AUS Stock')


class TransactionSerializerTest(APITestCase):
    """Tests for the Transaction serializer focusing on:
    1. Basic field serialization
    2. Calculated fields
    3. Read-only field protection
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.portfolio = self.user.portfolio
        
        self.transaction = Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('150.00')
        )

    def test_transaction_serialization(self):
        """Test basic transaction serialization"""
        serializer = TransactionSerializer(self.transaction)
        data = serializer.data
        
        self.assertEqual(data['asset_symbol'], 'AAPL')
        self.assertEqual(data['transaction_type'], 'buy')
        self.assertEqual(Decimal(data['quantity']), Decimal('10.0'))
        self.assertEqual(Decimal(data['price']), Decimal('150.00'))
        self.assertTrue('timestamp' in data)
        self.assertEqual(Decimal(data['transaction_value']), Decimal('1500.00'))

    def test_read_only_fields(self):
        """Test that read-only fields cannot be modified"""
        future_timestamp = timezone.now() + timezone.timedelta(days=1)
        
        data = {
            'asset_symbol': 'AAPL',
            'transaction_type': 'buy',
            'quantity': '10.0',
            'price': '150.00',
            'timestamp': future_timestamp,          # Should be read-only
            'transaction_value': '9999.99'          # Should be read-only
        }
        
        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Verify read-only fields are not included in validated data
        self.assertNotIn('timestamp', serializer.validated_data)
        self.assertNotIn('transaction_value', serializer.validated_data)


class PortfolioSerializerTest(APITestCase):
    """Tests for the Portfolio serializer focusing on:
    1. Nested serialization
    2. Calculated fields
    3. Read-only field protection
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.portfolio = self.user.portfolio
        
        # Create sample assets
        self.asset1 = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('10.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        self.asset2 = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='BTC-USD',
            name='Bitcoin',
            asset_type='crypto',
            position=Decimal('2.0'),
            last_price=Decimal('30000.00'),
            sector='Cryptocurrency'
        )
        
        # Create sample transaction
        self.transaction = Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('100.00')
        )

    def test_portfolio_serialization(self):
        """Test complete portfolio serialization with nested objects"""
        serializer = PortfolioSerializer(self.portfolio)
        data = serializer.data
        
        # Test main portfolio fields
        self.assertIn('id', data)
        self.assertIn('user', data)
        self.assertIn('assets', data)
        self.assertIn('transactions', data)
        
        # Test nested user data
        self.assertEqual(data['user']['username'], 'testuser')
        
        # Test nested assets
        self.assertEqual(len(data['assets']), 2)
        self.assertEqual(data['assets'][0]['symbol'], 'AAPL')
        self.assertEqual(data['assets'][1]['symbol'], 'BTC-USD')
        
        # Test nested transactions
        self.assertEqual(len(data['transactions']), 1)
        self.assertEqual(data['transactions'][0]['asset_symbol'], 'AAPL')

    def test_calculated_fields(self):
        """Test portfolio-level calculated fields"""
        serializer = PortfolioSerializer(self.portfolio)
        data = serializer.data
        
        # Expected values:
        # AAPL: 10 * 150 = 1500
        # BTC: 2 * 30000 = 60000
        # Total value: 61500
        self.assertEqual(Decimal(data['assets_value']), Decimal('61500.00'))
        
        # Cost is from AAPL transaction only: 10 * 100 = 1000
        self.assertEqual(Decimal(data['assets_cost']), Decimal('1000.00'))

    def test_read_only_fields(self):
        """Test that read-only fields cannot be modified"""
        data = {
            'id': 999,                    # Should be read-only
            'assets_value': '9999.99',    # Should be read-only
            'assets_cost': '9999.99'      # Should be read-only
        }
        
        serializer = PortfolioSerializer(self.portfolio, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        # Verify read-only fields are not included in validated data
        self.assertNotIn('id', serializer.validated_data)
        self.assertNotIn('assets_value', serializer.validated_data)
        self.assertNotIn('assets_cost', serializer.validated_data)