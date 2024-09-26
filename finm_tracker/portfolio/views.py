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
    context = {
        'portfolio': portfolio,
        'recent_transactions': portfolio.transactions.all().order_by('-timestamp')[:5]
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

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'portfolio/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def assets_view(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    assets = Asset.objects.filter(portfolio=portfolio)
    context = {'assets': assets}
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
            transaction, asset = PortfolioService.add_transaction(
                portfolio=portfolio,
                asset_symbol=request.POST['asset_symbol'],
                transaction_type=request.POST['transaction_type'],
                quantity=Decimal(request.POST['quantity']),
                price=Decimal(request.POST['price']),
                timestamp=timezone.now()
            )
            return redirect('transactions')
        except (ValidationError, InvalidOperation) as e:
            error_message = str(e)
            return render(request, 'portfolio/add_transaction.html', {'error': error_message})
    return render(request, 'portfolio/add_transaction.html')