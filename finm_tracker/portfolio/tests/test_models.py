from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ..models import Portfolio, Asset, Transaction
from decimal import Decimal
from django.utils import timezone
from ..templatetags.custom_filters import (
    multiply,
    display_decimal,
    profit_loss_color,
    remove_usd_suffix
)

User = get_user_model()

class PortfolioModelTest(TestCase):
    """Tests for the Portfolio model focusing on:
    1. Basic CRUD operations
    2. One-to-one relationship with User
    3. Portfolio value calculations
    4. Edge cases
    """
    
    def setUp(self):
        """Create a test user for all portfolio tests"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_portfolio_creation(self):
        """Test automatic portfolio creation via signals and string representation"""
        portfolio = self.user.portfolio
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio.user, self.user)
        self.assertEqual(str(portfolio), "testuser's Portfolio")

    def test_one_to_one_relationship(self):
        """Verify that a user cannot have multiple portfolios"""
        with self.assertRaises(IntegrityError):
            Portfolio.objects.create(user=self.user)
            
    def test_portfolio_assets_value(self):
        """Test portfolio total value calculation across multiple assets"""
        Asset.objects.create(
            portfolio=self.user.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('10.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        Asset.objects.create(
            portfolio=self.user.portfolio,
            symbol='BTC-USD',
            name='Bitcoin',
            asset_type='crypto',
            position=Decimal('2.0'),
            last_price=Decimal('30000.00'),
            sector='Cryptocurrency'
        )
        
        expected_value = Decimal('61500.00')  # (10 * 150) + (2 * 30000)
        self.assertEqual(self.user.portfolio.assets_value, expected_value)
        self.assertEqual(display_decimal(self.user.portfolio.assets_value), '61500.00')

    def test_portfolio_assets_cost(self):
        """Test portfolio total cost basis calculation"""
        Asset.objects.create(
            portfolio=self.user.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('10.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        Transaction.objects.create(
            portfolio=self.user.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('100.00')
        )
        
        expected_cost = Decimal('1000.00')  # 10 * 100
        self.assertEqual(self.user.portfolio.assets_cost, expected_cost)

    def test_empty_portfolio_values(self):
        """Test that a portfolio with no assets returns zero for calculations"""
        self.assertEqual(self.user.portfolio.assets_value, Decimal('0.00'))
        self.assertEqual(self.user.portfolio.assets_cost, Decimal('0.00'))

    def test_portfolio_with_no_prices(self):
        """Test portfolio calculations when assets have no prices set"""
        Asset.objects.create(
            portfolio=self.user.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('10.0'),
            last_price=None,  # No price set
            sector='Technology'
        )
        self.assertEqual(self.user.portfolio.assets_value, Decimal('0.00'))

class AssetModelTest(TestCase):
    """Tests for the Asset model focusing on:
    1. Asset creation and validation
    2. Financial calculations
    3. Edge cases and error conditions
    """
    
    def setUp(self):
        """Create a test user and portfolio for all asset tests"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.portfolio = self.user.portfolio

    def test_asset_creation(self):
        """Test basic asset creation and string representation"""
        asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL-USD',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('10.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        self.assertEqual(str(asset), "AAPL-USD - Apple Inc (10.0)")
        self.assertEqual(asset.symbol, 'AAPL-USD')
        self.assertEqual(asset.asset_type, 'stock_us')
        self.assertEqual(remove_usd_suffix(asset.symbol), 'AAPL')
        
    def test_asset_validation(self):
        """Test validation rules for asset creation"""
        # Test negative position
        with self.assertRaises(ValidationError):
            asset = Asset(
                portfolio=self.portfolio,
                symbol='GOOGL',
                name='Google',
                asset_type='stock_us',
                position=Decimal('-1.0'),
                last_price=Decimal('150.00'),
                sector='Technology'
            )
            asset.full_clean()
            
        # Test negative price
        with self.assertRaises(ValidationError):
            asset = Asset(
                portfolio=self.portfolio,
                symbol='GOOGL',
                name='Google',
                asset_type='stock_us',
                position=Decimal('1.0'),
                last_price=Decimal('-150.00'),
                sector='Technology'
            )
            asset.full_clean()

    def test_asset_type_validation(self):
        """Test that only valid asset types are accepted"""
        with self.assertRaises(ValidationError):
            asset = Asset(
                portfolio=self.portfolio,
                symbol='INVALID',
                name='Invalid Asset',
                asset_type='invalid_type',  # Invalid type
                position=Decimal('1.0'),
                last_price=Decimal('100.00'),
                sector='Technology'
            )
            asset.full_clean()

    def test_unique_portfolio_symbol_constraint(self):
        """Test that the same symbol cannot be added twice to a portfolio"""
        Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('10.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        with self.assertRaises(IntegrityError):
            Asset.objects.create(
                portfolio=self.portfolio,
                symbol='AAPL',
                name='Apple Inc',
                asset_type='stock_us',
                position=Decimal('5.0'),
                last_price=Decimal('150.00'),
                sector='Technology'
            )

    def test_profit_loss_calculation(self):
        """Test profit/loss calculations with various scenarios"""
        # Create asset with initial position
        asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('10.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        # Add buy transaction at lower price
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('100.00')
        )
        
        # Expected profit: Current value (1500) - Cost basis (1000) = 500
        expected_profit = Decimal('500.00')
        self.assertEqual(asset.profit_loss, expected_profit)
        
        # Test profit/loss formatting and color
        self.assertTrue('color: #059669' in profit_loss_color(asset.profit_loss))

    def test_zero_position_calculations(self):
        """Test financial calculations for assets with zero position"""
        asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('0.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        self.assertEqual(asset.market_value, Decimal('0.00'))
        self.assertEqual(asset.average_cost, Decimal('0.00'))

class TransactionModelTest(TestCase):
    """Tests for the Transaction model focusing on:
    1. Transaction creation and validation
    2. Buy/sell sequences
    3. Transaction value calculations
    """
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.portfolio = self.user.portfolio

    def test_transaction_creation(self):
        """Test basic transaction creation and string representation"""
        transaction = Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL-USD',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('150.00')
        )
        
        self.assertEqual(str(transaction), "buy 10.0 AAPL-USD at 150.00")
        self.assertEqual(remove_usd_suffix(transaction.asset_symbol), 'AAPL')

    def test_transaction_validation(self):
        """Test validation rules for transactions"""
        with self.assertRaises(ValidationError):
            transaction = Transaction(
                portfolio=self.portfolio,
                asset_symbol='AAPL-USD',
                transaction_type='buy',
                quantity=Decimal('-1.0'),
                price=Decimal('150.00')
            )
            transaction.full_clean()

    def test_transaction_value(self):
        """Test transaction value calculations"""
        transaction = Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL-USD',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('150.00')
        )
        
        expected_value = Decimal('1500.00')  # 10 * 150
        self.assertEqual(transaction.transaction_value, expected_value)
        self.assertEqual(
            multiply(float(transaction.quantity), float(transaction.price)),
            float(expected_value)
        )

    def test_unique_timestamp_constraint(self):
        """Test that transactions must have unique timestamps"""
        timestamp = timezone.now()
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL-USD',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('150.00'),
            timestamp=timestamp
        )
        
        with self.assertRaises(IntegrityError):
            Transaction.objects.create(
                portfolio=self.portfolio,
                asset_symbol='AAPL-USD',
                transaction_type='buy',
                quantity=Decimal('5.0'),
                price=Decimal('150.00'),
                timestamp=timestamp
            )

    def test_buy_sell_sequence(self):
        """Test a sequence of buy and sell transactions"""
        # Initial buy
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('100.00')
        )
        
        # Sell half
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='sell',
            quantity=Decimal('5.0'),
            price=Decimal('150.00')
        )
        
        asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('5.0'),  # Remaining position after sell
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        # Test remaining cost basis: (10 * 100) - (5 * 150) = 250
        expected_cost = Decimal('250.00')
        self.assertEqual(asset.total_cost, expected_cost)
        
        # Test average cost per share: 250 / 5 = 50
        expected_avg_cost = Decimal('50.00')
        self.assertEqual(asset.average_cost, expected_avg_cost)

class CustomFiltersTest(TestCase):
    """Tests for custom template filters"""
    
    def test_display_decimal(self):
        """Test decimal display formatting"""
        self.assertEqual(display_decimal(Decimal('100')), '100.00')
        self.assertEqual(display_decimal(Decimal('100.10')), '100.1')
        self.assertEqual(display_decimal(Decimal('0')), '0.00')
        
    def test_profit_loss_color(self):
        """Test profit/loss color formatting"""
        self.assertEqual(profit_loss_color(Decimal('100')), 'style="color: #059669;"')
        self.assertEqual(profit_loss_color(Decimal('-100')), 'style="color: #e11d48;"')
        
    def test_remove_usd_suffix(self):
        """Test USD suffix removal from symbols"""
        self.assertEqual(remove_usd_suffix('BTC-USD'), 'BTC')
        self.assertEqual(remove_usd_suffix('AAPL'), 'AAPL')

class PortfolioIntegrationTest(TestCase):
    """Integration tests for Portfolio, Asset, and Transaction interactions"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.portfolio = self.user.portfolio

    def test_portfolio_update_after_transactions(self):
        """Test that portfolio values update correctly after transactions"""
        # Create initial asset
        asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('0.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        # Add buy transaction
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('100.00')
        )
        
        # Update asset position
        asset.position = Decimal('10.0')
        asset.save()
        
        # Verify portfolio values
        self.assertEqual(self.portfolio.assets_value, Decimal('1500.00'))
        self.assertEqual(self.portfolio.assets_cost, Decimal('1000.00'))
        
        # Add sell transaction
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='sell',
            quantity=Decimal('5.0'),
            price=Decimal('150.00')
        )
        
        # Update asset position
        asset.position = Decimal('5.0')
        asset.save()
        
        # Verify updated portfolio values
        self.assertEqual(self.portfolio.assets_value, Decimal('750.00'))
        self.assertEqual(self.portfolio.assets_cost, Decimal('250.00'))

    def test_multiple_asset_types_handling(self):
        """Test portfolio handling of different asset types simultaneously"""
        # Create stock asset
        Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('10.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        # Create crypto asset
        Asset.objects.create(
            portfolio=self.portfolio,
            symbol='BTC-USD',
            name='Bitcoin',
            asset_type='crypto',
            position=Decimal('2.0'),
            last_price=Decimal('30000.00'),
            sector='Cryptocurrency'
        )
        
        # Create Australian stock
        Asset.objects.create(
            portfolio=self.portfolio,
            symbol='BHP.AX',
            name='BHP Group',
            asset_type='stock_au',
            position=Decimal('100.0'),
            last_price=Decimal('40.00'),
            sector='Materials'
        )
        
        # Test total portfolio value calculation across different asset types
        expected_value = Decimal('65500.00000000')  # (10 * 150) + (2 * 30000) + (100 * 40)
        self.assertEqual(self.portfolio.assets_value, expected_value)

    def test_mixed_transaction_history(self):
        """Test portfolio behavior with mixed transaction types across multiple assets"""
        # Create two assets
        aapl = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('0.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        btc = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='BTC-USD',
            name='Bitcoin',
            asset_type='crypto',
            position=Decimal('0.0'),
            last_price=Decimal('30000.00'),
            sector='Cryptocurrency'
        )
        
        # Create transactions for both assets
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('100.00')
        )
        
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='BTC-USD',
            transaction_type='buy',
            quantity=Decimal('2.0'),
            price=Decimal('25000.00')
        )
        
        # Update positions
        aapl.position = Decimal('10.0')
        btc.position = Decimal('2.0')
        aapl.save()
        btc.save()
        
        # Verify individual asset values
        self.assertEqual(aapl.market_value, Decimal('1500.00'))
        self.assertEqual(btc.market_value, Decimal('60000.00'))
        
        # Verify portfolio totals
        self.assertEqual(self.portfolio.assets_value, Decimal('61500.00'))
        self.assertEqual(self.portfolio.assets_cost, Decimal('51000.00'))  # (10 * 100) + (2 * 25000)

    def test_transaction_ordering(self):
        """Test that transactions maintain correct chronological ordering"""
        # Create transactions with specific timestamps
        t1 = timezone.now() - timezone.timedelta(days=2)
        t2 = timezone.now() - timezone.timedelta(days=1)
        t3 = timezone.now()
        
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('5.0'),
            price=Decimal('100.00'),
            timestamp=t2
        )
        
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('3.0'),
            price=Decimal('90.00'),
            timestamp=t1
        )
        
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='sell',
            quantity=Decimal('2.0'),
            price=Decimal('110.00'),
            timestamp=t3
        )
        
        transactions = self.portfolio.transactions.all().order_by('timestamp')
        self.assertEqual(transactions[0].quantity, Decimal('3.0'))
        self.assertEqual(transactions[1].quantity, Decimal('5.0'))
        self.assertEqual(transactions[2].quantity, Decimal('2.0'))