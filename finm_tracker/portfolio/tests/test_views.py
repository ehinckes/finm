from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from portfolio.models import Portfolio, Asset, Transaction
from rest_framework.authtoken.models import Token


User = get_user_model()

class PortfolioViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_portfolio_already_exists(self):
        # Check that a portfolio already exists for the user
        self.assertTrue(hasattr(self.user, 'portfolio'))
        self.assertIsNotNone(self.user.portfolio)

    def test_create_duplicate_portfolio(self):
        # Attempt to create a new portfolio
        url = reverse('portfolio-list')
        response = self.client.post(url, {})
        
        # Check that the request was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify the error message
        self.assertIn("A portfolio already exists for this user.", str(response.data))
        
        # Ensure only one portfolio exists for the user
        self.assertEqual(Portfolio.objects.filter(user=self.user).count(), 1)

class AssetViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.portfolio = self.user.portfolio

    def test_create_asset(self):
        url = reverse('asset-list')
        data = {'symbol': 'AAPL', 'name': 'Apple Inc.', 'quantity': 10, 'asset_type': 'stock'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Asset.objects.count(), 1)
        asset = Asset.objects.first()
        self.assertEqual(asset.symbol, 'AAPL')
        self.assertEqual(asset.name, 'Apple Inc.')
        self.assertEqual(asset.quantity, 10)
        self.assertEqual(asset.asset_type, 'stock')
        self.assertEqual(asset.portfolio, self.portfolio)


class TransactionViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.portfolio = self.user.portfolio
        self.asset = Asset.objects.create(portfolio=self.portfolio, symbol='AAPL', name='Apple Inc.', asset_type='stock', quantity=100, current_price=150.00)

    def test_authentication_required(self):
        self.client.credentials()  # Remove authentication
        url = reverse('transaction-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_buy_transaction(self):
        url = reverse('transaction-list')
        data = {
            'asset_symbol': 'AAPL',
            'transaction_type': 'buy',
            'quantity': 10,
            'price': 150.00
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.asset_symbol, 'AAPL')
        self.assertEqual(transaction.transaction_type, 'buy')
        self.assertEqual(transaction.quantity, 10)
        self.assertEqual(transaction.price, 150.00)

    def test_create_sell_transaction(self):
        url = reverse('transaction-list')
        data = {
            'asset_symbol': 'AAPL',
            'transaction_type': 'sell',
            'quantity': 10,
            'price': 160.00
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.asset_symbol, 'AAPL')
        self.assertEqual(transaction.transaction_type, 'sell')
        self.assertEqual(transaction.quantity, 10)
        self.assertEqual(transaction.price, 160.00)

    def test_service_error_handling(self):
        url = reverse('transaction-list')
        data = {
            'asset_symbol': 'INVALID',
            'transaction_type': 'buy',
            'quantity': -10,
            'price': -100.00
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)