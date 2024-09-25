from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Portfolio, Asset, Transaction
from .serializers import PortfolioSerializer, AssetSerializer, TransactionSerializer
from django.shortcuts import get_object_or_404
from .services.portfolio_services import PortfolioService
from rest_framework.exceptions import ValidationError
from django.utils import timezone


class PortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)

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

    def get_queryset(self):
        return Transaction.objects.filter(portfolio__user=self.request.user)

    def perform_create(self, serializer):
        portfolio = get_object_or_404(Portfolio, user=self.request.user)
        
        try:
            transaction, asset = PortfolioService.add_transaction(
                portfolio=portfolio,
                asset_symbol=serializer.validated_data['asset_symbol'],
                transaction_type=serializer.validated_data['transaction_type'],
                quantity=serializer.validated_data['quantity'],
                price=serializer.validated_data['price'],
                timestamp=timezone.now()  # Pass the timestamp to the service
            )
            serializer.instance = transaction
            serializer.save(portfolio=portfolio, timestamp=transaction.timestamp)
        except ValidationError as e:
            error_message = str(e)
            if "Cannot sell an asset that is not in the portfolio" in error_message:
                raise serializers.ValidationError("You cannot sell an asset that you don't own.")
            elif "Insufficient asset quantity for sale" in error_message:
                raise serializers.ValidationError("You don't have enough of this asset to complete the sale.")
            else:
                raise serializers.ValidationError(error_message)

    @action(detail=False, methods=['post'])
    def buy(self, request):
        return self._process_transaction(request, 'buy')

    @action(detail=False, methods=['post'])
    def sell(self, request):
        return self._process_transaction(request, 'sell')

    def _process_transaction(self, request, transaction_type):
        portfolio = get_object_or_404(Portfolio, user=request.user)
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(portfolio=portfolio, transaction_type=transaction_type)
            
            # Update asset quantity
            asset = get_object_or_404(Asset, portfolio=portfolio, symbol=serializer.validated_data['asset_symbol'])
            quantity_change = serializer.validated_data['quantity']
            
            if transaction_type == 'buy':
                asset.quantity += quantity_change
            else:  # sell
                if asset.quantity < quantity_change:
                    return Response({"error": "Insufficient asset quantity for sale"}, status=status.HTTP_400_BAD_REQUEST)
                asset.quantity -= quantity_change
            
            asset.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)