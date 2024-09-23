from rest_framework import serializers
from .models import CustomUser
from portfolio.serializers import PortfolioSerializer

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    portfolio = PortfolioSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password', 'portfolio')

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user