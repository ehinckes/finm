# users/tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

class TestCustomUser(TestCase):
    """
    Test cases for the CustomUser model.
    """
    
    def setUp(self):
        """
        Set up test data before each test method.
        """
        self.User = get_user_model()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_create_user(self):
        """Test creating a new user with valid data"""
        user = self.User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, self.user_data['username'])
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertEqual(user.last_name, self.user_data['last_name'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a new superuser"""
        admin_user = self.User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_active)

    def test_user_string_representation(self):
        """Test the string representation of user"""
        user = self.User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data['username'])

    def test_user_email_normalized(self):
        """Test email is normalized when user is created"""
        email = 'test@EXAMPLE.COM'
        user = self.User.objects.create_user(
            username='test2',
            email=email,
            password='test123'
        )
        self.assertEqual(user.email, email.lower())

    def test_user_without_username_fails(self):
        """Test creating user without username raises error"""
        with self.assertRaises(ValueError):
            self.User.objects.create_user(
                username='',
                email='test@example.com',
                password='test123'
            )

    def test_duplicate_username_fails(self):
        """Test creating user with duplicate username fails"""
        self.User.objects.create_user(**self.user_data)
        with self.assertRaises(IntegrityError):
            self.User.objects.create_user(**self.user_data)

    def test_long_username_fails(self):
        """Test creating user with username > 150 chars fails"""
        user = self.User(
            username='a' * 151,
            email='test@example.com',
            password='test123'
        )
        with self.assertRaises(ValidationError):
            # Validate the model before trying to save it
            user.full_clean()