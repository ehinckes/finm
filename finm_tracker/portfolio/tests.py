from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Asset, Transaction
from decimal import Decimal
from datetime import datetime, timezone

class AssetAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
        self.asset_data = {
            'name': 'Test Stock',
            'symbol': 'TST',
            'asset_type': 'STOCK',
            'quantity': '100.00',
        }
        self.url = reverse('asset-list')

    def test_create_asset(self):
        response = self.client.post(self.url, self.asset_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Asset.objects.count(), 1)
        self.assertEqual(Asset.objects.get().name, 'Test Stock')
        self.assertEqual(Asset.objects.get().user, self.user)

    def test_create_asset_invalid_data(self):
        invalid_data = self.asset_data.copy()
        invalid_data['quantity'] = 'not a number'
        response = self.client.post(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_asset_list(self):
        Asset.objects.create(user=self.user, **self.asset_data)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_asset_detail(self):
        asset = Asset.objects.create(user=self.user, **self.asset_data)
        url = reverse('asset-detail', kwargs={'pk': asset.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.asset_data['name'])

    def test_update_asset(self):
        asset = Asset.objects.create(user=self.user, **self.asset_data)
        url = reverse('asset-detail', kwargs={'pk': asset.pk})
        updated_data = {'name': 'Updated Stock', 'quantity': '150.00'}
        response = self.client.patch(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Asset.objects.get(pk=asset.pk).name, 'Updated Stock')
        self.assertEqual(Asset.objects.get(pk=asset.pk).quantity, Decimal('150.00'))

    def test_delete_asset(self):
        asset = Asset.objects.create(user=self.user, **self.asset_data)
        url = reverse('asset-detail', kwargs={'pk': asset.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Asset.objects.count(), 0)

    def test_create_asset_missing_fields(self):
        incomplete_data = {'name': 'Incomplete Stock'}
        response = self.client.post(self.url, incomplete_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_duplicate_asset(self):
        Asset.objects.create(user=self.user, **self.asset_data)
        response = self.client.post(self.url, self.asset_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Asset.objects.count(), 2)

    def test_get_nonexistent_asset(self):
        url = reverse('asset-detail', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_asset_invalid_data(self):
        asset = Asset.objects.create(user=self.user, **self.asset_data)
        url = reverse('asset-detail', kwargs={'pk': asset.pk})
        invalid_data = {'quantity': 'not a number'}
        response = self.client.patch(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_asset_list_ordering(self):
        Asset.objects.create(user=self.user, name='C Stock', symbol='C', asset_type='STOCK', quantity='100.00')
        Asset.objects.create(user=self.user, name='A Stock', symbol='A', asset_type='STOCK', quantity='100.00')
        Asset.objects.create(user=self.user, name='B Stock', symbol='B', asset_type='STOCK', quantity='100.00')
        
        # Test default ordering (by name)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], 'A Stock')
        self.assertEqual(response.data[2]['name'], 'C Stock')

        # Test explicit ordering by name descending
        response = self.client.get(f"{self.url}?ordering=-name")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], 'C Stock')
        self.assertEqual(response.data[2]['name'], 'A Stock')

        # Test ordering by symbol
        response = self.client.get(f"{self.url}?ordering=symbol")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['symbol'], 'A')
        self.assertEqual(response.data[2]['symbol'], 'C')


class TransactionAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
        self.asset = Asset.objects.create(
            user=self.user,
            name='Test Stock',
            symbol='TST',
            asset_type='STOCK',
            quantity='100.00'
        )
        self.transaction_data = {
            'asset': self.asset,  # Use the Asset instance instead of its ID
            'transaction_type': 'BUY',
            'quantity': '10.00',
            'price': '50.00',
        }
        self.url = reverse('transaction-list')

    def test_create_transaction(self):
        data = self.transaction_data.copy()
        data['asset'] = self.asset.id  # Use asset ID for API request
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Transaction.objects.get().transaction_type, 'BUY')
        self.assertEqual(Transaction.objects.get().user, self.user)

    def test_create_transaction_invalid_data(self):
        invalid_data = self.transaction_data.copy()
        invalid_data['quantity'] = 'not a number'
        invalid_data['asset'] = self.asset.id  # Use asset ID for API request
        response = self.client.post(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_transaction_list(self):
        Transaction.objects.create(user=self.user, **self.transaction_data)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_transaction_detail(self):
        transaction = Transaction.objects.create(user=self.user, **self.transaction_data)
        url = reverse('transaction-detail', kwargs={'pk': transaction.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['transaction_type'], self.transaction_data['transaction_type'])

    def test_update_transaction(self):
        transaction = Transaction.objects.create(user=self.user, **self.transaction_data)
        url = reverse('transaction-detail', kwargs={'pk': transaction.pk})
        updated_data = {'quantity': '15.00', 'price': '55.00'}
        response = self.client.patch(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Transaction.objects.get(pk=transaction.pk).quantity, Decimal('15.00'))
        self.assertEqual(Transaction.objects.get(pk=transaction.pk).price, Decimal('55.00'))

    def test_delete_transaction(self):
        transaction = Transaction.objects.create(user=self.user, **self.transaction_data)
        url = reverse('transaction-detail', kwargs={'pk': transaction.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_transaction_list_ordering(self):
        Transaction.objects.create(user=self.user, asset=self.asset, transaction_type='BUY', quantity='10.00', price='50.00', date=datetime(2023, 1, 1, tzinfo=timezone.utc))
        Transaction.objects.create(user=self.user, asset=self.asset, transaction_type='SELL', quantity='5.00', price='60.00', date=datetime(2023, 2, 1, tzinfo=timezone.utc))
        Transaction.objects.create(user=self.user, asset=self.asset, transaction_type='BUY', quantity='15.00', price='45.00', date=datetime(2023, 3, 1, tzinfo=timezone.utc))
        
        # Test default ordering (by date descending)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['quantity'], '15.00')
        self.assertEqual(response.data[2]['quantity'], '10.00')

        # Test explicit ordering by quantity
        response = self.client.get(f"{self.url}?ordering=quantity")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['quantity'], '5.00')
        self.assertEqual(response.data[2]['quantity'], '15.00')

        # Test ordering by transaction_type
        response = self.client.get(f"{self.url}?ordering=transaction_type")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['transaction_type'], 'BUY')
        self.assertEqual(response.data[2]['transaction_type'], 'SELL')