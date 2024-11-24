from django.apps import AppConfig

class PortfolioConfig(AppConfig):
    """
    Configuration class for the Portfolio application.
    This class is used by Django to configure the app-specific settings
    and perform initialization tasks.
    """
    # Specifies the primary key type for models that don't define a primary key
    # BigAutoField provides a 64-bit integer, allowing for a larger range of values
    default_auto_field = 'django.db.models.BigAutoField'
    
    # The name of the application as it should be referenced in Django settings
    # and other parts of the Django framework
    name = 'portfolio'
    
    def ready(self):
        """
        Method called by Django when the application is ready to be used.
        This is where we connect signal handlers to ensure they are registered
        when the application starts.
        
        Imports the signals module to register all signal handlers defined there.
        Note: This import is done here to avoid circular imports.
        """
        import portfolio.signals