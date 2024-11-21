from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Currently maintains default AbstractUser fields with no additional fields.
    Can be extended in the future for custom functionality.
    
    Inherits from AbstractUser:
        - username
        - first_name
        - last_name
        - email
        - password
        - groups
        - user_permissions
        - is_staff
        - is_active
        - is_superuser
        - last_login
        - date_joined
    """
    
    # No additional fields needed at the moment
    # Ready for future customization
    
    def __str__(self):
        """
        String representation of the user.
        
        Returns:
            str: The username of the user
        """
        return self.username
    
    class Meta:
        """
        Meta options for the CustomUser model.
        """
        verbose_name = 'User'
        verbose_name_plural = 'Users'