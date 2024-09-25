from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from portfolio.models import Portfolio, Asset, Transaction
from decimal import Decimal
from unittest.mock import patch
from django.core.exceptions import ValidationError

User = get_user_model()

class PortfolioViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_create_first_portfolio(self):
        url = reverse('portfolio-list')
        data = {}  # No additional data needed as user is set automatically
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Portfolio.objects.count(), 1)

    def test_create_duplicate_portfolio(self):
        # Create the first portfolio
        Portfolio.objects.create(user=self.user)

        # Try to create a second portfolio
        url = reverse('portfolio-list')
        data = {}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("A portfolio already exists for this user.", str(response.data))
        self.assertEqual(Portfolio.objects.count(), 1)

class AssetViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.portfolio = Portfolio.objects.create(user=self.user)

    def test_create_asset(self):
        url = reverse('asset-list')
        data = {
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'asset_type': 'stock',
            'quantity': '10.5',
            'current_price': '150.75'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Asset.objects.count(), 1)
        self.assertEqual(Asset.objects.first().symbol, 'AAPL')

class TransactionViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.portfolio = Portfolio.objects.create(user=self.user)
        self.asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='stock',
            quantity=Decimal('10'),
            current_price=Decimal('150.75')
        )

    def test_create_buy_transaction(self):
        url = reverse('transaction-list')
        data = {
            'asset_symbol': 'AAPL',
            'transaction_type': 'buy',
            'quantity': '5',
            'price': '160.00'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_create_sell_transaction(self):
        url = reverse('transaction-list')
        data = {
            'asset_symbol': 'AAPL',
            'transaction_type': 'sell',
            'quantity': '5',
            'price': '160.00'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)

    @patch('portfolio.services.portfolio_services.PortfolioService.add_transaction')
    def test_service_error_handling(self, mock_add_transaction):
        url = reverse('transaction-list')
        data = {
            'asset_symbol': 'AAPL',
            'transaction_type': 'sell',
            'quantity': '15',
            'price': '160.00'
        }
        
        # Test handling of "Insufficient asset quantity for sale" error
        mock_add_transaction.side_effect = ValidationError("Insufficient asset quantity for sale")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You don't have enough of this asset to complete the sale.", str(response.data))

        # Test handling of "Cannot sell an asset that is not in the portfolio" error
        mock_add_transaction.side_effect = ValidationError("Cannot sell an asset that is not in the portfolio")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You cannot sell an asset that you don't own.", str(response.data))

        # Test handling of other ValidationErrors
        mock_add_transaction.side_effect = ValidationError("Some other error")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Some other error", str(response.data))

    def test_authentication_required(self):
        self.client.force_authenticate(user=None)
        url = reverse('transaction-list')
        data = {
            'asset_symbol': 'AAPL',
            'transaction_type': 'buy',
            'quantity': '5',
            'price': '160.00'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)