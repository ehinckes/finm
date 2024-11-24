from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Portfolio

# Get the active User model as specified in settings.AUTH_USER_MODEL
User = get_user_model()

@receiver(post_save, sender=User)
def create_user_portfolio(sender, instance, created, **kwargs):
    """
    Signal handler to automatically create a Portfolio when a new User is created.
    
    Args:
        sender: The model class that sent the signal (User model)
        instance: The actual instance being saved (User instance)
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments passed to the signal
    
    This ensures every user has an associated portfolio as soon as they register.
    Uses get_or_create to prevent duplicate portfolios if the signal is triggered multiple times.
    """
    if created:  # Only execute when a new user is created, not on updates
        Portfolio.objects.get_or_create(user=instance)