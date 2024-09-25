from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from portfolio.models import Portfolio, Asset, Transaction
from portfolio.services.portfolio_services import PortfolioService

User = get_user_model()

class PortfolioServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.portfolio = Portfolio.objects.create(user=self.user)

    def test_add_buy_transaction_new_asset(self):
        transaction, asset = PortfolioService.add_transaction(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10'),
            price=Decimal('150.75'),
            timestamp=timezone.now()
        )

        self.assertEqual(Asset.objects.count(), 1)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(asset.symbol, 'AAPL')
        self.assertEqual(asset.quantity, Decimal('10'))
        self.assertEqual(asset.current_price, Decimal('150.75'))
        self.assertEqual(transaction.transaction_type, 'buy')

    def test_add_buy_transaction_existing_asset(self):
        Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='stock',
            quantity=Decimal('5'),
            current_price=Decimal('145.00')
        )

        transaction, asset = PortfolioService.add_transaction(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10'),
            price=Decimal('150.75'),
            timestamp=timezone.now()
        )

        self.assertEqual(Asset.objects.count(), 1)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(asset.quantity, Decimal('15'))
        self.assertEqual(asset.current_price, Decimal('150.75'))

    def test_add_sell_transaction(self):
        Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='stock',
            quantity=Decimal('20'),
            current_price=Decimal('145.00')
        )

        transaction, asset = PortfolioService.add_transaction(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='sell',
            quantity=Decimal('10'),
            price=Decimal('150.75'),
            timestamp=timezone.now()
        )

        self.assertEqual(Asset.objects.count(), 1)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(asset.quantity, Decimal('10'))
        self.assertEqual(asset.current_price, Decimal('150.75'))
        self.assertEqual(transaction.transaction_type, 'sell')

    def test_sell_non_existent_asset(self):
        with self.assertRaises(ValidationError) as context:
            PortfolioService.add_transaction(
                portfolio=self.portfolio,
                asset_symbol='AAPL',
                transaction_type='sell',
                quantity=Decimal('10'),
                price=Decimal('150.75'),
                timestamp=timezone.now()
            )
        
        self.assertIn("Cannot sell an asset that is not in the portfolio", str(context.exception))

    def test_sell_more_than_owned(self):
        Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='stock',
            quantity=Decimal('5'),
            current_price=Decimal('145.00')
        )

        with self.assertRaises(ValidationError) as context:
            PortfolioService.add_transaction(
                portfolio=self.portfolio,
                asset_symbol='AAPL',
                transaction_type='sell',
                quantity=Decimal('10'),
                price=Decimal('150.75'),
                timestamp=timezone.now()
            )
        
        self.assertIn("Insufficient asset quantity for sale", str(context.exception))

    def test_invalid_transaction_type(self):
        with self.assertRaises(ValidationError) as context:
            PortfolioService.add_transaction(
                portfolio=self.portfolio,
                asset_symbol='AAPL',
                transaction_type='invalid',
                quantity=Decimal('10'),
                price=Decimal('150.75'),
                timestamp=timezone.now()
            )
        
        self.assertIn("Invalid transaction type", str(context.exception))

    def test_fetch_asset_info(self):
        asset_info = PortfolioService.fetch_asset_info('AAPL')
        self.assertEqual(asset_info['name'], 'Asset AAPL')
        self.assertEqual(asset_info['asset_type'], 'stock')

    def test_buy_zero_quantity(self):
        with self.assertRaises(ValidationError) as context:
            PortfolioService.add_transaction(
                portfolio=self.portfolio,
                asset_symbol='AAPL',
                transaction_type='buy',
                quantity=Decimal('0'),
                price=Decimal('150.75'),
                timestamp=timezone.now()
            )
        
        self.assertIn("Transaction quantity must be greater than zero", str(context.exception))

    def test_negative_price(self):
        with self.assertRaises(ValidationError) as context:
            PortfolioService.add_transaction(
                portfolio=self.portfolio,
                asset_symbol='AAPL',
                transaction_type='buy',
                quantity=Decimal('10'),
                price=Decimal('-150.75'),
                timestamp=timezone.now()
            )
        
        self.assertIn("Transaction price must be greater than zero", str(context.exception))