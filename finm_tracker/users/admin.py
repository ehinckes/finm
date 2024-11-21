from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    """
    Custom admin interface for CustomUser model.
    Extends Django's UserAdmin for enhanced user management.
    """
    
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    
    # Extend default UserAdmin fieldsets
    # Currently no additional fields, but structure is ready for future extensions
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ()}),
    )

admin.site.register(CustomUser, CustomUserAdmin)