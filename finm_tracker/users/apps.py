from django.apps import AppConfig

class UsersConfig(AppConfig):
    """
    Configuration class for the users application.
    Handles app-specific configuration and initialization.
    """
    
    # Use BigAutoField for primary keys
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'