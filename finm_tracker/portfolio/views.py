from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Portfolio, Asset, Transaction
from .serializers import PortfolioSerializer, AssetSerializer, TransactionSerializer
from .services.portfolio_services import PortfolioService
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from decimal import Decimal, InvalidOperation
from django.contrib.auth import get_user_model
from django import forms
import json



class PortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        if Portfolio.objects.filter(user=request.user).exists():
            return Response({"detail": "A portfolio already exists for this user."}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AssetViewSet(viewsets.ModelViewSet):
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Asset.objects.filter(portfolio__user=self.request.user)

    def perform_create(self, serializer):
        portfolio = get_object_or_404(Portfolio, user=self.request.user)
        serializer.save(portfolio=portfolio)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        return Transaction.objects.filter(portfolio__user=self.request.user)

    def create(self, request, *args, **kwargs):
        
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        portfolio, created = Portfolio.objects.get_or_create(user=self.request.user)
        transaction, asset = PortfolioService.add_transaction(
            portfolio=portfolio,
            asset_symbol=serializer.validated_data['asset_symbol'],
            transaction_type=serializer.validated_data['transaction_type'],
            quantity=serializer.validated_data['quantity'],
            price=serializer.validated_data['price'],
            timestamp=serializer.validated_data.get('timestamp')
        )
        serializer.instance = transaction


@login_required
def home_view(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    
    # Update prices before calculating portfolio values
    update_summary = PortfolioService.update_portfolio_prices(portfolio)
    daily_gainers = PortfolioService.fetch_daily_gainers()
    
    # Calculate portfolio value and P&L
    portfolio_value = portfolio.assets_value
    portfolio_cost = portfolio.assets_cost
    portfolio_pl = portfolio_value - portfolio_cost

    # Get asset allocation data for pie chart, grouped by sector
    assets = Asset.objects.filter(portfolio=portfolio)
    sector_allocation = {}
    for asset in assets:
        if asset.market_value > 0:
            if asset.sector not in sector_allocation:
                sector_allocation[asset.sector] = 0
            sector_allocation[asset.sector] += float(asset.market_value)
    
    # Convert sector_allocation to list of dictionaries
    sector_allocation_list = [
        {
            'name': sector,
            'value': value,
            'color': f'#{hash(sector) % 0xFFFFFF:06x}'  # Generate a color based on the sector name
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
        'prices_updated': not update_summary['cached'],  # Indicates if prices were freshly updated
        'update_summary': update_summary,  # Include update summary in context
    }
    return render(request, 'portfolio/home.html', context)


def login_view(request):
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


User = get_user_model()
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-full px-3 py-2 border border-custom-green-light rounded focus:outline-none focus:ring-2 focus:ring-custom-green-full'

def register_view(request):
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
    logout(request)
    return redirect('login')

@login_required
def assets_view(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    
    # Clear cache if force update requested
    if request.GET.get('force_update'):
        cache.delete(f'portfolio_prices_{portfolio.id}')
    
    # Update prices before displaying assets
    update_summary = PortfolioService.update_portfolio_prices(portfolio)
    
    assets = Asset.objects.filter(portfolio=portfolio)

    # Filtering
    asset_types = ['all', 'stock_us', 'stock_au', 'crypto']
    current_filter = request.GET.get('asset_type', 'all').lower()
    if current_filter not in asset_types:
        current_filter = 'all'
    
    if current_filter != 'all':
        assets = assets.filter(asset_type=current_filter)

    # Sorting
    sort_by = request.GET.get('sort', 'symbol')
    assets = assets.order_by(sort_by)

    # Total value calculation
    total_value = sum(asset.market_value for asset in assets)

    # Total profit loss calculation
    total_profit_loss = sum(asset.profit_loss for asset in assets)

    # Determine display text for asset type and filter
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
        'prices_updated': not update_summary['cached'],  # Indicates if prices were freshly updated
        'update_summary': update_summary,  # Include update summary in context
    }
    return render(request, 'portfolio/assets.html', context)

@login_required
def transactions_view(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    transactions = Transaction.objects.filter(portfolio=portfolio)
    context = {'transactions': transactions}
    return render(request, 'portfolio/transactions.html', context)

@login_required
def add_transaction_view(request):
    if request.method == 'POST':
        portfolio = get_object_or_404(Portfolio, user=request.user)
        try:
            use_current_time = request.POST.get('use_current_time') == 'on'
            if use_current_time:
                timestamp = timezone.now()
            else:
                custom_timestamp = request.POST.get('custom_timestamp')
                if custom_timestamp:
                    timestamp = timezone.make_aware(timezone.datetime.strptime(custom_timestamp, '%Y-%m-%dT%H:%M'))
                else:
                    raise ValidationError("Custom timestamp is required when not using current time.")
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
def performance_view(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    context = {
        'portfolio': portfolio,
    }
    return render(request, 'portfolio/performance.html', context)



@login_required
def risks_view(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    context = {
        'portfolio': portfolio,
    }
    return render(request, 'portfolio/risks.html', context)

@login_required
def projections_view(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    context = {
        'portfolio': portfolio,
    }
    return render(request, 'portfolio/projections.html', context)


