from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from portfolio.models import Portfolio, Asset, Transaction
from portfolio.serializers import AssetSerializer, TransactionSerializer, PortfolioSerializer
from decimal import Decimal

User = get_user_model()

class AssetSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.portfolio = self.user.portfolio
        self.asset_data = {
            'portfolio': self.portfolio,
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'asset_type': 'stock',
            'quantity': Decimal('10.5'),
            'current_price': Decimal('150.75')
        }
        self.asset = Asset.objects.create(**self.asset_data)
        self.serializer = AssetSerializer(instance=self.asset)

    def test_contains_expected_fields(self):
        data = self.serializer.data
        self.assertEqual(set(data.keys()), set(['id', 'symbol', 'name', 'asset_type', 'quantity', 'current_price', 'current_value', 'profit_loss']))

    def test_symbol_field_content(self):
        data = self.serializer.data
        self.assertEqual(data['symbol'], self.asset_data['symbol'])

    def test_quantity_field_content(self):
        data = self.serializer.data
        self.assertEqual(Decimal(data['quantity']), self.asset_data['quantity'])

class TransactionSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.portfolio = self.user.portfolio
        self.transaction_data = {
            'portfolio': self.portfolio,
            'asset_symbol': 'AAPL',
            'transaction_type': 'buy',
            'quantity': Decimal('5.0'),
            'price': Decimal('150.00')
        }
        self.transaction = Transaction.objects.create(**self.transaction_data)
        self.serializer = TransactionSerializer(instance=self.transaction)

    def test_contains_expected_fields(self):
        data = self.serializer.data
        self.assertEqual(set(data.keys()), set(['id', 'timestamp', 'asset_symbol', 'transaction_type', 'quantity', 'price', 'current_value']))

    def test_asset_symbol_field_content(self):
        data = self.serializer.data
        self.assertEqual(data['asset_symbol'], self.transaction_data['asset_symbol'])

    def test_quantity_field_content(self):
        data = self.serializer.data
        self.assertEqual(Decimal(data['quantity']), self.transaction_data['quantity'])

class PortfolioSerializerTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.portfolio = self.user.portfolio
        self.asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='stock',
            quantity=Decimal('10.5'),
            current_price=Decimal('150.75')
        )
        self.transaction = Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('5.0'),
            price=Decimal('150.00')
        )
        self.serializer = PortfolioSerializer(instance=self.portfolio)

    def test_contains_expected_fields(self):
        data = self.serializer.data
        self.assertEqual(set(data.keys()), set(['id', 'user', 'assets', 'transactions', 'assets_value', 'assets_cost']))

    def test_assets_field_content(self):
        data = self.serializer.data
        self.assertEqual(len(data['assets']), 1)
        self.assertEqual(data['assets'][0]['symbol'], 'AAPL')

    def test_transactions_field_content(self):
        data = self.serializer.data
        self.assertEqual(len(data['transactions']), 1)
        self.assertEqual(data['transactions'][0]['asset_symbol'], 'AAPL')

    def test_user_field_content(self):
        data = self.serializer.data
        self.assertEqual(data['user']['username'], 'testuser')