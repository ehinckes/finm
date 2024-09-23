from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from .models import Portfolio, Asset, Transaction
from users.models import CustomUser
from .serializers import PortfolioSerializer, AssetSerializer, TransactionSerializer

class ModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='12345')
        self.portfolio = Portfolio.objects.get(user=self.user)
        self.asset = Asset.objects.create(
            portfolio=self.portfolio,
            name='Test Stock',
            symbol='TST',
            asset_type='STOCK',
            quantity=10,
            current_price=100.00
        )

    def test_custom_user_creation(self):
        self.assertTrue(isinstance(self.user, CustomUser))
        self.assertEqual(str(self.user), 'testuser')

    def test_portfolio_creation(self):
        self.assertTrue(isinstance(self.portfolio, Portfolio))
        self.assertEqual(str(self.portfolio), "testuser's Portfolio")

    def test_asset_creation(self):
        self.assertTrue(isinstance(self.asset, Asset))
        self.assertEqual(str(self.asset), "Test Stock (TST)")

    def test_transaction_creation_buy(self):
        transaction = Transaction.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            transaction_type='BUY',
            quantity=5,
            price=100.00
        )
        self.assertTrue(isinstance(transaction, Transaction))
        self.assertEqual(str(transaction), "Buy 5.00 TST at 100.00")
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.quantity, 15)

    def test_transaction_creation_sell(self):
        transaction = Transaction.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            transaction_type='SELL',
            quantity=5,
            price=100.00
        )
        self.assertTrue(isinstance(transaction, Transaction))
        self.assertEqual(str(transaction), "Sell 5.00 TST at 100.00")
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.quantity, 5)

    def test_transaction_creation_sell_more_than_owned(self):
        with self.assertRaises(ValueError):
            Transaction.objects.create(
                portfolio=self.portfolio,
                asset=self.asset,
                transaction_type='SELL',
                quantity=15,
                price=100.00
            )

class SerializerTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='12345')
        self.portfolio = Portfolio.objects.get(user=self.user)
        self.asset = Asset.objects.create(
            portfolio=self.portfolio,
            name='Test Stock',
            symbol='TST',
            asset_type='STOCK',
            quantity=10,
            current_price=100.00
        )
        self.transaction = Transaction.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            transaction_type='BUY',
            quantity=5,
            price=100.00
        )

    def test_portfolio_serializer(self):
        serializer = PortfolioSerializer(instance=self.portfolio)
        self.assertEqual(set(serializer.data.keys()), {'id', 'user', 'assets', 'transactions'})

    def test_asset_serializer(self):
        serializer = AssetSerializer(instance=self.asset)
        self.assertEqual(set(serializer.data.keys()), {'id', 'name', 'symbol', 'asset_type', 'quantity', 'current_price'})

    def test_transaction_serializer(self):
        serializer = TransactionSerializer(instance=self.transaction)
        self.assertEqual(set(serializer.data.keys()), {'id', 'asset', 'transaction_type', 'quantity', 'price', 'date'})

class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(username='testuser', password='12345')
        self.client.force_authenticate(user=self.user)
        self.portfolio = Portfolio.objects.get(user=self.user)
        self.asset = Asset.objects.create(
            portfolio=self.portfolio,
            name='Test Stock',
            symbol='TST',
            asset_type='STOCK',
            quantity=10,
            current_price=100.00
        )

    def test_get_portfolio(self):
        url = reverse('portfolio-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user.id)

    def test_get_assets(self):
        url = reverse('asset-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_asset(self):
        url = reverse('asset-list')
        data = {
            'name': 'New Stock',
            'symbol': 'NEW',
            'asset_type': 'STOCK',
            'quantity': 5,
            'current_price': 50.00
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Asset.objects.count(), 2)

    def test_create_asset_invalid_data(self):
        url = reverse('asset-list')
        data = {
            'name': 'Invalid Stock',
            'symbol': 'INV',
            'asset_type': 'INVALID',  # Invalid asset type
            'quantity': 5,
            'current_price': 50.00
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_asset(self):
        url = reverse('asset-detail', args=[self.asset.id])
        data = {
            'name': 'Updated Stock',
            'symbol': 'UPD',
            'asset_type': 'STOCK',
            'quantity': 15,
            'current_price': 150.00
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.name, 'Updated Stock')

    def test_delete_asset(self):
        url = reverse('asset-detail', args=[self.asset.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Asset.objects.count(), 0)

    def test_get_transactions(self):
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            transaction_type='BUY',
            quantity=5,
            price=100.00
        )
        url = reverse('transaction-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_transaction(self):
        url = reverse('transaction-list')
        data = {
            'asset': self.asset.id,
            'transaction_type': 'BUY',
            'quantity': 5,
            'price': 100.00
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.quantity, 15)

    def test_create_transaction_sell_more_than_owned(self):
        url = reverse('transaction-list')
        data = {
            'asset': self.asset.id,
            'transaction_type': 'SELL',
            'quantity': 15,
            'price': 100.00
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class AuthorizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = CustomUser.objects.create_user(username='user1', password='12345')
        self.user2 = CustomUser.objects.create_user(username='user2', password='12345')
        self.portfolio1 = Portfolio.objects.get(user=self.user1)
        self.portfolio2 = Portfolio.objects.get(user=self.user2)
        self.asset1 = Asset.objects.create(
            portfolio=self.portfolio1,
            name='User1 Stock',
            symbol='US1',
            asset_type='STOCK',
            quantity=10,
            current_price=100.00
        )
        self.asset2 = Asset.objects.create(
            portfolio=self.portfolio2,
            name='User2 Stock',
            symbol='US2',
            asset_type='STOCK',
            quantity=10,
            current_price=100.00
        )

    def test_user_can_access_own_portfolio(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('portfolio-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user1.id)

    def test_user_cannot_access_other_user_portfolio(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('asset-detail', args=[self.asset2.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_cannot_access_portfolio(self):
        url = reverse('portfolio-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)