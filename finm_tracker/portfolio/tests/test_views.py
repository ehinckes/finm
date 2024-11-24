from unittest.mock import patch
from django.forms import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from django.utils import timezone
from ..models import Portfolio, Asset, Transaction
from ..serializers import PortfolioSerializer, AssetSerializer, TransactionSerializer
import json
import unittest

User = get_user_model()

class PortfolioViewSetTest(APITestCase):
    """Tests for the Portfolio ViewSet focusing on:
    1. Authentication requirements
    2. CRUD operations
    3. User-specific portfolio filtering
    4. Multiple portfolio prevention
    """

    def setUp(self):
        """Create test users and initial data"""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        self.portfolio1 = self.user1.portfolio  # Created by signal
        
    def test_list_portfolio_authentication(self):
        """Test that authentication is required for portfolio access"""
        response = self.client.get(reverse('portfolio-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('portfolio-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_portfolio_list_filtering(self):
        """Test that users can only see their own portfolio"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('portfolio-list'))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user']['username'], 'testuser1')

    def test_prevent_multiple_portfolios(self):
        """Test that users cannot create multiple portfolios"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse('portfolio-list'), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', str(response.data['detail']))

class AssetViewSetTest(APITestCase):
    """Tests for the Asset ViewSet focusing on:
    1. Authentication requirements
    2. CRUD operations
    3. Portfolio-based filtering
    4. Asset creation validation
    """

    def setUp(self):
        """Create test user, portfolio, and sample asset"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.portfolio = self.user.portfolio
        
        self.asset_data = {
            'symbol': 'AAPL',
            'name': 'Apple Inc',
            'asset_type': 'stock_us',
            'position': '10.0',
            'last_price': '150.00',
            'sector': 'Technology'
        }
        
        self.asset = Asset.objects.create(
            portfolio=self.portfolio,
            **self.asset_data
        )

    def test_asset_list_authentication(self):
        """Test that authentication is required for asset access"""
        response = self.client.get(reverse('asset-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('asset-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_asset_creation(self):
        """Test asset creation through API"""
        self.client.force_authenticate(user=self.user)
        new_asset_data = {
            'symbol': 'GOOGL',
            'name': 'Google Inc',
            'asset_type': 'stock_us',
            'position': '5.0',
            'last_price': '2500.00',
            'sector': 'Technology'
        }
        
        response = self.client.post(reverse('asset-list'), new_asset_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['symbol'], 'GOOGL')

    def test_asset_detail(self):
        """Test retrieving specific asset details"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse('asset-detail', kwargs={'pk': self.asset.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['symbol'], 'AAPL')

    def test_asset_update(self):
        """Test updating asset information"""
        self.client.force_authenticate(user=self.user)
        update_data = {'last_price': '160.00'}
        
        response = self.client.patch(
            reverse('asset-detail', kwargs={'pk': self.asset.pk}),
            update_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['last_price']), Decimal('160.00'))

class TransactionViewSetTest(APITestCase):
    """Tests for the Transaction ViewSet focusing on:
    1. Authentication requirements
    2. Request validation
    3. Basic CRUD operations
    4. Error responses
    """

    def setUp(self):
        """Create test user, portfolio, and sample transaction"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.portfolio = self.user.portfolio
        
        # Create an asset first
        self.asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('0.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        self.transaction_data = {
            'asset_symbol': 'AAPL',
            'asset_type': 'stock_us',
            'transaction_type': 'buy',
            'quantity': '10.0',
            'price': '150.00'
        }

    def test_transaction_list_authentication(self):
        """Test that authentication is required for transaction access"""
        response = self.client.get(reverse('transaction-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('transaction-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('portfolio.services.portfolio_services.PortfolioService.add_transaction')
    def test_transaction_creation(self, mock_add_transaction):
        """Test basic transaction creation through the API"""
        self.client.force_authenticate(user=self.user)
        
        # Mock the service layer response
        mock_transaction = Transaction(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('150.00')
        )
        mock_add_transaction.return_value = (mock_transaction, self.asset)
        
        response = self.client.post(reverse('transaction-list'), self.transaction_data)
        
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response data: {response.data}")  # For debugging
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['asset_symbol'], 'AAPL')
        mock_add_transaction.assert_called_once()

    @patch('portfolio.services.portfolio_services.PortfolioService.add_transaction')
    def test_invalid_transaction_creation(self, mock_add_transaction):
        """Test validation errors in transaction creation"""
        self.client.force_authenticate(user=self.user)
        
        # Mock the service layer to raise ValidationError
        mock_add_transaction.side_effect = ValidationError("Invalid transaction")
        
        invalid_data = {
            'asset_symbol': 'AAPL',
            'asset_type': 'stock_us',
            'transaction_type': 'buy',
            'quantity': '-10.0',  # Invalid negative quantity
            'price': '150.00'
        }
        
        response = self.client.post(reverse('transaction-list'), invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_missing_fields(self):
        """Test transaction creation with missing required fields"""
        self.client.force_authenticate(user=self.user)
        incomplete_data = {
            'asset_symbol': 'AAPL',
            'transaction_type': 'buy'
            # Missing quantity and price
        }
        
        response = self.client.post(reverse('transaction-list'), incomplete_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transaction_list_filtering(self):
        """Test that users can only see their own transactions"""
        # Create another user with a transaction
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        Transaction.objects.create(
            portfolio=other_user.portfolio,
            asset_symbol='GOOGL',
            transaction_type='buy',
            quantity=Decimal('5.0'),
            price=Decimal('150.00')
        )
        
        # Create a transaction for test user
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('100.00')
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('transaction-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Should only see own transaction
        self.assertEqual(response.data[0]['asset_symbol'], 'AAPL')


class PortfolioViewsTest(TestCase):
    """Tests for traditional Django views focusing on:
    1. Authentication requirements
    2. Template rendering
    3. Context data
    4. Form handling
    """

    def setUp(self):
        """Create test user, portfolio, and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.portfolio = self.user.portfolio
        
        # Create sample asset and transaction
        self.asset = Asset.objects.create(
            portfolio=self.portfolio,
            symbol='AAPL',
            name='Apple Inc',
            asset_type='stock_us',
            position=Decimal('10.0'),
            last_price=Decimal('150.00'),
            sector='Technology'
        )
        
        self.transaction = Transaction.objects.create(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            transaction_type='buy',
            quantity=Decimal('10.0'),
            price=Decimal('100.00')
        )

    def test_home_view(self):
        """Test home view rendering and context"""
        # Test unauthenticated access
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test authenticated access
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portfolio/home.html')
        
        # Test context data
        self.assertIn('portfolio', response.context)
        self.assertIn('portfolio_value', response.context)
        self.assertIn('portfolio_pl', response.context)

    def test_assets_view(self):
        """Test assets view with filtering and sorting"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test default view
        response = self.client.get(reverse('assets'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portfolio/assets.html')
        
        # Test filtering
        response = self.client.get(f"{reverse('assets')}?asset_type=stock_us")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['assets']), 1)
        
        # Test sorting
        response = self.client.get(f"{reverse('assets')}?sort=symbol")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_sort'], 'symbol')

    def test_add_transaction_view(self):
        """Test transaction creation through form"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test GET request
        response = self.client.get(reverse('add_transaction'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'portfolio/add_transaction.html')
        
        # Test POST request
        transaction_data = {
            'asset_symbol': 'AAPL',
            'asset_type': 'stock_us',
            'transaction_type': 'buy',
            'quantity': '5.0',
            'price': '150.00',
            'use_current_time': 'on'
        }
        
        response = self.client.post(reverse('add_transaction'), transaction_data)
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(Transaction.objects.filter(
            portfolio=self.portfolio,
            asset_symbol='AAPL',
            quantity=Decimal('5.0')
        ).exists())