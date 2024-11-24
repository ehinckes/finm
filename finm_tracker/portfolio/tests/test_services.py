from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock
from ..models import Portfolio, Asset, Transaction
from ..services.portfolio_services import PortfolioService
from ..services.external_api_service import ExternalAPIService

User = get_user_model()

class PortfolioServiceTest(TestCase):
    """
    Tests for PortfolioService focusing on transaction processing
    and portfolio management.
    """
    
    def setUp(self):
        """Create test user and portfolio with initial assets"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.portfolio = self.user.portfolio
        
        # Mock asset info that would come from external API
        self.mock_asset_info = {
            'name': 'Apple Inc',
            'last_price': Decimal('150.00'),
            'sector': 'Technology'
        }

    @patch.object(ExternalAPIService, 'fetch_asset_info')
    def test_add_new_buy_transaction(self, mock_fetch_asset_info):
        """Test buying a new asset not currently in portfolio"""
        mock_fetch_asset_info.return_value = self.mock_asset_info
        
        transaction, asset = PortfolioService.add_transaction(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            asset_type='stock_us',
            transaction_type='buy',
            quantity='10.0',
            price='150.00',
            timestamp=timezone.now()
        )
        
        # Verify transaction created correctly
        self.assertEqual(transaction.asset_symbol, 'AAPL')
        self.assertEqual(transaction.quantity, Decimal('10.0'))
        self.assertEqual(transaction.price, Decimal('150.00'))
        
        # Verify asset created correctly
        self.assertEqual(asset.symbol, 'AAPL')
        self.assertEqual(asset.position, Decimal('10.0'))
        self.assertEqual(asset.asset_type, 'stock_us')

    def test_add_to_existing_position(self):
        """Test buying more of an existing asset"""
        # Create initial position
        asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('10.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        # Add to position
        transaction, updated_asset = PortfolioService.add_transaction(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            asset_type='stock_us',
            transaction_type='buy',
            quantity='5.0',
            price='160.00',
            timestamp=timezone.now()
        )
        
        # Verify position updated correctly
        self.assertEqual(updated_asset.position, Decimal('15.0'))
        self.assertEqual(transaction.quantity, Decimal('5.0'))

    def test_valid_sell_transaction(self):
        """Test selling part of an existing position"""
        # Create initial position
        asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('10.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        # Sell part of position
        transaction, updated_asset = PortfolioService.add_transaction(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            asset_type='stock_us',
            transaction_type='sell',
            quantity='4.0',
            price='160.00',
            timestamp=timezone.now()
        )
        
        # Verify position reduced correctly
        self.assertEqual(updated_asset.position, Decimal('6.0'))
        self.assertEqual(transaction.transaction_type, 'sell')

    def test_sell_without_position(self):
        """Test selling an asset not in portfolio"""
        with self.assertRaises(ValidationError):
            PortfolioService.add_transaction(
                portfolio=self.portfolio,
                asset_symbol='AAPL',
                asset_type='stock_us',
                transaction_type='sell',
                quantity='10.0',
                price='150.00',
                timestamp=timezone.now()
            )

    def test_sell_more_than_owned(self):
        """Test selling more than current position"""
        # Create initial position
        asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('5.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        with self.assertRaises(ValidationError):
            PortfolioService.add_transaction(
                portfolio=self.portfolio,
                asset_symbol='AAPL',
                asset_type='stock_us',
                transaction_type='sell',
                quantity='10.0',
                price='160.00',
                timestamp=timezone.now()
            )

    def test_invalid_transaction_parameters(self):
        """Test various invalid transaction parameters"""
        # Test negative quantity
        with self.assertRaises(ValidationError):
            PortfolioService.add_transaction(
                portfolio=self.portfolio,
                asset_symbol='AAPL',
                asset_type='stock_us',
                transaction_type='buy',
                quantity='-10.0',
                price='150.00',
                timestamp=timezone.now()
            )
        
        # Test negative price
        with self.assertRaises(ValidationError):
            PortfolioService.add_transaction(
                portfolio=self.portfolio,
                asset_symbol='AAPL',
                asset_type='stock_us',
                transaction_type='buy',
                quantity='10.0',
                price='-150.00',
                timestamp=timezone.now()
            )
        
        # Test future timestamp
        future_time = timezone.now() + timezone.timedelta(days=1)
        with self.assertRaises(ValidationError):
            PortfolioService.add_transaction(
                portfolio=self.portfolio,
                asset_symbol='AAPL',
                asset_type='stock_us',
                transaction_type='buy',
                quantity='10.0',
                price='150.00',
                timestamp=future_time
            )

    def test_symbol_standardization(self):
        """Test symbol standardization for different asset types"""
        # Test ASX symbol standardization
        with patch.object(ExternalAPIService, 'fetch_asset_info') as mock_fetch:
            mock_fetch.return_value = {
                'name': 'BHP Group',
                'last_price': Decimal('40.00'),
                'sector': 'Materials'
            }
            
            transaction, asset = PortfolioService.add_transaction(
                portfolio=self.portfolio,
                asset_symbol='BHP',
                asset_type='stock_au',
                transaction_type='buy',
                quantity='100.0',
                price='40.00',
                timestamp=timezone.now()
            )
            
            self.assertEqual(asset.symbol, 'BHP.AX')
        
        # Test crypto symbol standardization
        with patch.object(ExternalAPIService, 'fetch_asset_info') as mock_fetch:
            mock_fetch.return_value = {
                'name': 'Bitcoin',
                'last_price': Decimal('30000.00'),
                'sector': 'Cryptocurrency'
            }
            
            transaction, asset = PortfolioService.add_transaction(
                portfolio=self.portfolio,
                asset_symbol='BTC',
                asset_type='crypto',
                transaction_type='buy',
                quantity='1.0',
                price='30000.00',
                timestamp=timezone.now()
            )
            
            self.assertEqual(asset.symbol, 'BTC-USD')