from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from .permissions import IsOwnerOrReadOnly

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling user-related operations.
    Provides CRUD operations and custom actions for user management.
    
    Endpoints:
        - GET /users/ : List users (filtered to current user only)
        - POST /users/ : Create user
        - GET /users/{id}/ : Retrieve user
        - PUT /users/{id}/ : Update user
        - DELETE /users/{id}/ : Delete user
        - GET /users/me/ : Get current user
        - POST /users/register/ : Register new user
    """
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_permissions(self):
        """
        Instantiate and return the list of permissions that this view requires.
        'register' action doesn't require authentication.
        """
        if self.action == 'register':
            return []
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        """
        Get the list of items for this view.
        For list action, returns only the current user's data.
        For other actions, returns all users (subject to permissions).
        
        Returns:
            QuerySet: Filtered queryset based on the action
        """
        if self.action == 'list':
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Custom endpoint to retrieve the current user's details.
        
        Args:
            request: The HTTP request object
            
        Returns:
            Response: Serialized data of the current user
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """
        Custom create method to properly handle password hashing.
        
        Args:
            serializer: The UserSerializer instance with validated data
        """
        user = serializer.save()
        user.set_password(serializer.validated_data['password'])
        user.save()

    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Custom registration endpoint that allows unauthenticated access.
        
        Args:
            request: The HTTP request object containing user data
            
        Returns:
            Response: Created user data or validation errors
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)