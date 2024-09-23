from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    pass  # No additional fields needed atm

    def __str__(self):
        return self.username