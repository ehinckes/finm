from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

# Get the User model specified in settings.AUTH_USER_MODEL
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model that handles user creation and updates.
    Includes fields for user identification, contact information, and secure password handling.
    """
    
    # Password field is write-only for security and uses Django's password validation
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        help_text="Required. Must meet system password requirements."
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']
        read_only_fields = ['id']  # ID is auto-generated and should not be modifiable

    def create(self, validated_data):
        """
        Create and return a new user instance, given the validated data.
        Uses create_user instead of create to ensure proper password hashing.

        Args:
            validated_data (dict): Dictionary of validated user data

        Returns:
            User: Newly created user instance
        """
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        """
        Update and return an existing user instance, given the validated data.
        Handles password updates separately to ensure proper hashing.

        Args:
            instance (User): Existing user instance
            validated_data (dict): Dictionary of validated user data

        Returns:
            User: Updated user instance
        """
        # Extract password before update as it needs special handling
        password = validated_data.pop('password', None)
        
        # Update all other fields
        user = super().update(instance, validated_data)
        
        # If password was included in the data, hash it and save
        if password:
            user.set_password(password)
            user.save()
            
        return user