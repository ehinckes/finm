from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ..models import Portfolio, Asset, Transaction
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

class PortfolioModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_portfolio_creation(self):
        portfolio = self.user.portfolio
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio.user, self.user)
        self.assertEqual(str(portfolio), "testuser's Portfolio")

    def test_one_to_one_relationship(self):
        with self.assertRaises(IntegrityError):
            Portfolio.objects.create(user=self.user)

class AssetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.portfolio = self.user.portfolio

    def test_asset_creation(self):
        asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='stock',
            quantity=Decimal('10'),
            current_price=Decimal('150.00')
        )
        self.assertEqual(asset.symbol, 'AAPL')
        self.assertEqual(asset.name, 'Apple Inc.')
        self.assertEqual(asset.asset_type, 'stock')
        self.assertEqual(asset.position, Decimal('10'))
        self.assertEqual(asset.last_price, Decimal('150.00'))
        self.assertEqual(str(asset), 'AAPL - Apple Inc. (10)')

    def test_negative_quantity_validation(self):
        asset = Asset(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='stock',
            quantity=Decimal('-10'),
            current_price=Decimal('150.00')
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_negative_price_validation(self):
        asset = Asset(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='stock',
            quantity=Decimal('10'),
            current_price=Decimal('-150.00')
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_unique_together_constraint(self):
        Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='stock',
            quantity=Decimal('10'),
            current_price=Decimal('150.00')
        )
        with self.assertRaises(IntegrityError):
            Asset.objects.create(
                portfolio=self.portfolio,
                symbol='AAPL',
                name='Apple Inc.',
                asset_type='stock',
                quantity=Decimal('5'),
                current_price=Decimal('155.00')
            )

class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.portfolio = self.user.portfolio

    def test_transaction_creation(self):
        transaction = Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10'),
            price=Decimal('150.00'),
            timestamp=timezone.now()
        )
        self.assertEqual(transaction.asset_symbol, 'AAPL')
        self.assertEqual(transaction.transaction_type, 'buy')
        self.assertEqual(transaction.quantity, Decimal('10'))
        self.assertEqual(transaction.price, Decimal('150.00'))
        self.assertEqual(str(transaction), 'buy 10 AAPL at 150.00')

    def test_negative_quantity_validation(self):
        transaction = Transaction(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('-10'),
            price=Decimal('150.00')
        )
        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_negative_price_validation(self):
        transaction = Transaction(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10'),
            price=Decimal('-150.00')
        )
        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_unique_together_constraint(self):
        transaction1 = Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10'),
            price=Decimal('150.00')
        )
        
        # Force the same timestamp
        same_timestamp = transaction1.timestamp
        
        with self.assertRaises(IntegrityError):
            Transaction.objects.create(
                portfolio=self.portfolio,
                asset_symbol='AAPL',
                transaction_type='buy',
                quantity=Decimal('5'),
                price=Decimal('155.00'),
                timestamp=same_timestamp
            )