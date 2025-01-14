# Django core imports
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.http import HttpResponse

# Django REST framework imports
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

# Local imports
from .models import Portfolio, Asset, Transaction
from .serializers import PortfolioSerializer, AssetSerializer, TransactionSerializer
from .services.portfolio_services import PortfolioService

# Other imports
from decimal import Decimal, InvalidOperation
from django.contrib.auth import get_user_model
from django import forms
import json
import csv


# API ViewSets
class PortfolioViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Portfolio-related API endpoints.
    Provides CRUD operations for portfolios with user-based filtering.
    """
    serializer_class = PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter portfolios to show only the requesting user's portfolio"""
        return Portfolio.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Override create method to prevent multiple portfolios per user
        Returns 400 if user already has a portfolio
        """
        if Portfolio.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "A portfolio already exists for this user."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Automatically set the user when creating a portfolio"""
        serializer.save(user=self.request.user)

class AssetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling Asset-related API endpoints.
    Provides CRUD operations for assets with portfolio-based filtering.
    """
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter assets to show only those in the user's portfolio"""
        return Asset.objects.filter(portfolio__user=self.request.user)

    def perform_create(self, serializer):
        """Automatically set the portfolio when creating an asset"""
        portfolio = get_object_or_404(Portfolio, user=self.request.user)
        serializer.save(portfolio=portfolio)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Filter transactions to show only those in the user's portfolio"""
        return Transaction.objects.filter(portfolio__user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Override create method to handle transaction creation with error handling
        Returns appropriate error responses for different failure scenarios
        """
        serializer = self.get_serializer(data=request.data)
        try:
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Log the error here if needed
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        """Create transaction and update related portfolio/asset data"""
        portfolio = Portfolio.objects.get(user=self.request.user)
        
        transaction, asset = PortfolioService.add_transaction(
            portfolio=portfolio,
            asset_symbol=serializer.validated_data['asset_symbol'],
            asset_type=serializer.validated_data.get('asset_type'),
            transaction_type=serializer.validated_data['transaction_type'],
            quantity=serializer.validated_data['quantity'],
            price=serializer.validated_data['price'],
            timestamp=serializer.validated_data.get('timestamp')
        )
        
        serializer.instance = transaction


# Portfolio Main Views
@login_required
def home_view(request):
    """
    Dashboard view showing portfolio overview, including:
    - Portfolio value and P&L
    - Asset allocation by sector
    - Recent transactions
    - Daily gainers
    - Price update status
    """
    portfolio = get_object_or_404(Portfolio, user=request.user)
    
    # Update portfolio prices and fetch market data
    update_summary = PortfolioService.update_portfolio_prices(portfolio)
    daily_gainers = PortfolioService.fetch_daily_gainers()
    
    # Calculate portfolio metrics
    portfolio_value = portfolio.assets_value
    portfolio_cost = portfolio.assets_cost
    portfolio_pl = portfolio_value - portfolio_cost

    # Calculate sector allocation for pie chart
    assets = Asset.objects.filter(portfolio=portfolio)
    sector_allocation = {}
    for asset in assets:
        if asset.market_value > 0:
            if asset.sector not in sector_allocation:
                sector_allocation[asset.sector] = 0
            sector_allocation[asset.sector] += float(asset.market_value)
    
    # Format sector allocation for frontend chart
    sector_allocation_list = [
        {
            'name': sector,
            'value': value,
            'color': f'#{hash(sector) % 0xFFFFFF:06x}'  # Generate unique color per sector
        }
        for sector, value in sector_allocation.items()
    ]
    
    context = {
        'portfolio': portfolio,
        'portfolio_value': portfolio_value,
        'portfolio_pl': portfolio_pl,
        'recent_transactions': portfolio.transactions.all().order_by('-timestamp')[:5],
        'daily_gainers': daily_gainers,
        'sector_allocation_json': json.dumps(sector_allocation_list),
        'prices_updated': not update_summary['cached'],
        'update_summary': update_summary,
    }
    return render(request, 'portfolio/home.html', context)

@login_required
def assets_view(request):
    """
    View for displaying and managing portfolio assets.
    Features:
    - Asset filtering by type
    - Sorting functionality
    - Price updates
    - Total value and P&L calculations
    """
    portfolio = get_object_or_404(Portfolio, user=request.user)
    
    # Handle force price update
    if request.GET.get('force_update'):
        cache.delete(f'portfolio_prices_{portfolio.id}')
    
    update_summary = PortfolioService.update_portfolio_prices(portfolio)
    assets = Asset.objects.filter(portfolio=portfolio)

    # Asset filtering
    asset_types = ['all', 'stock_us', 'stock_au', 'crypto']
    current_filter = request.GET.get('asset_type', 'all').lower()
    if current_filter not in asset_types:
        current_filter = 'all'
    
    if current_filter != 'all':
        assets = assets.filter(asset_type=current_filter)

    # Asset sorting
    sort_by = request.GET.get('sort', 'symbol')
    assets = assets.order_by(sort_by)

    # Calculate totals
    total_value = sum(asset.market_value for asset in assets)
    total_profit_loss = sum(asset.profit_loss for asset in assets)

    # Asset type display mapping
    asset_type_display_map = {
        'all': 'Assets',
        'stock_us': 'US Stock Assets',
        'stock_au': 'AUS Stock Assets',
        'crypto': 'Crypto Assets',
    }
    asset_type_display = asset_type_display_map[current_filter]
    button_text = 'All' if current_filter == 'all' else asset_type_display.split()[0]

    context = {
        'assets': assets,
        'total_value': total_value,
        'total_profit_loss': total_profit_loss,
        'current_sort': sort_by,
        'current_filter': current_filter,
        'asset_type_display': asset_type_display,
        'button_text': button_text,
        'prices_updated': not update_summary['cached'],
        'update_summary': update_summary,
    }
    return render(request, 'portfolio/assets.html', context)

@login_required
def add_transaction_view(request):
    """
    View for adding new transactions.
    Handles:
    - Transaction creation with custom or current timestamp
    - Input validation
    - Asset creation/update through PortfolioService
    """
    if request.method == 'POST':
        portfolio = get_object_or_404(Portfolio, user=request.user)
        try:
            # Handle timestamp selection
            use_current_time = request.POST.get('use_current_time') == 'on'
            if use_current_time:
                timestamp = timezone.now()
            else:
                custom_timestamp = request.POST.get('custom_timestamp')
                if custom_timestamp:
                    timestamp = timezone.make_aware(
                        timezone.datetime.strptime(custom_timestamp, '%Y-%m-%dT%H:%M')
                    )
                else:
                    raise ValidationError("Custom timestamp is required when not using current time.")

            # Create transaction through service layer
            transaction, asset = PortfolioService.add_transaction(
                portfolio=portfolio,
                asset_symbol=request.POST['asset_symbol'].upper(),
                asset_type=request.POST['asset_type'],
                transaction_type=request.POST['transaction_type'],
                quantity=Decimal(request.POST['quantity']),
                price=Decimal(request.POST['price']),
                timestamp=timestamp
            )
            return redirect('transactions')
        except (ValidationError, InvalidOperation) as e:
            error_message = str(e)
            return render(request, 'portfolio/add_transaction.html', {'error': error_message})
    return render(request, 'portfolio/add_transaction.html')

@login_required
def transactions_view(request):
    """View for displaying all portfolio transactions"""
    portfolio = get_object_or_404(Portfolio, user=request.user)
    transactions = Transaction.objects.filter(portfolio=portfolio)
    context = {'transactions': transactions}
    return render(request, 'portfolio/transactions.html', context)


# Authentication Views and Forms
User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """
    Extended user registration form that includes email field
    and custom styling for form widgets.
    """
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        """Initialize form and add custom Tailwind CSS classes to all fields"""
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'w-full px-3 py-2 border border-custom-green-light '
                'rounded focus:outline-none focus:ring-2 focus:ring-custom-green-full'
            )

def login_view(request):
    """
    Handle user login with Django's built-in authentication form.
    On successful login, redirects to home page.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'portfolio/login.html', {'form': form})

def register_view(request):
    """
    Handle user registration using CustomUserCreationForm.
    On successful registration, logs user in and redirects to home page.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'portfolio/register.html', {'form': form})

@login_required
def logout_view(request):
    """Handle user logout and redirect to login page"""
    logout(request)
    return redirect('login')


# Analysis Views
@login_required
def performance_view(request):
    """
    View for displaying portfolio performance metrics.
    TODO: Implement detailed performance analysis
    """
    portfolio = get_object_or_404(Portfolio, user=request.user)
    context = {
        'portfolio': portfolio,
    }
    return render(request, 'portfolio/performance.html', context)

@login_required
def risks_view(request):
    """
    View for displaying portfolio risk metrics.
    TODO: Implement risk analysis calculations
    """
    portfolio = get_object_or_404(Portfolio, user=request.user)
    context = {
        'portfolio': portfolio,
    }
    return render(request, 'portfolio/risks.html', context)

@login_required
def projections_view(request):
    """
    View for displaying portfolio projections.
    TODO: Implement future value projections
    """
    portfolio = get_object_or_404(Portfolio, user=request.user)
    context = {
        'portfolio': portfolio,
    }
    return render(request, 'portfolio/projections.html', context)


# Utility Views
@login_required
def export_transactions_csv(request):
    """
    Export portfolio transactions as CSV file.
    Includes:
    - Timestamp
    - Asset
    - Transaction Type
    - Quantity
    - Price
    - Total Value
    """
    # Set up CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    # Create CSV writer and write headers
    writer = csv.writer(response)
    writer.writerow([
        'Timestamp',
        'Asset',
        'Type',
        'Quantity',
        'Price',
        'Total'
    ])

    # Get user's portfolio transactions and write to CSV
    portfolio = get_object_or_404(Portfolio, user=request.user)
    transactions = Transaction.objects.filter(portfolio=portfolio).order_by('-timestamp')
    
    for transaction in transactions:
        writer.writerow([
            transaction.timestamp.strftime("%d/%m/%Y, %H:%M:%S"),
            transaction.asset_symbol,
            transaction.get_transaction_type_display(),
            transaction.quantity,
            f"{transaction.price:.2f}",
            f"{transaction.transaction_value:.2f}"
        ])
    
    return response