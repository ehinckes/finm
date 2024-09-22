from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from .models import Asset, Transaction
from .serializers import AssetSerializer, TransactionSerializer

class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['name', 'symbol', 'asset_type', 'quantity']
    ordering = ['name']  # Default ordering

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['date', 'asset__symbol', 'transaction_type', 'quantity', 'price']
    ordering = ['-date']  # Default ordering, most recent first

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)