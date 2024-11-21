from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from ..serializers import UserSerializer
from rest_framework import serializers

# Get the custom user model or default Django user model
User = get_user_model()

class UserSerializerTest(TestCase):
    """
    Test suite for the UserSerializer class.
    Tests all aspects of user serialization including:
    - Field validation
    - User creation
    - User updates
    - Password handling
    - Data security
    """

    def setUp(self):
        """
        Initialize test data before each test method.
        Creates a test user and initializes the serializer.
        """
        # Define standard test user attributes
        self.user_attributes = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
        # Create a test user in the database
        self.user = User.objects.create_user(**self.user_attributes)
        # Initialize the serializer with the test user
        self.serializer = UserSerializer(instance=self.user)

    def test_contains_expected_fields(self):
        """
        Verify that the serialized data contains all expected fields.
        Password should not be included in serialized output.
        """
        data = self.serializer.data
        expected_fields = set(['id', 'username', 'email', 'first_name', 'last_name'])
        self.assertEqual(set(data.keys()), expected_fields)

    def test_username_field_content(self):
        """
        Verify that the username field is correctly serialized.
        """
        data = self.serializer.data
        self.assertEqual(data['username'], self.user_attributes['username'])

    def test_email_field_content(self):
        """
        Verify that the email field is correctly serialized.
        """
        data = self.serializer.data
        self.assertEqual(data['email'], self.user_attributes['email'])

    def test_first_name_field_content(self):
        """
        Verify that the first_name field is correctly serialized.
        """
        data = self.serializer.data
        self.assertEqual(data['first_name'], self.user_attributes['first_name'])

    def test_last_name_field_content(self):
        """
        Verify that the last_name field is correctly serialized.
        """
        data = self.serializer.data
        self.assertEqual(data['last_name'], self.user_attributes['last_name'])

    def test_password_field_not_included(self):
        """
        Verify that the password field is not included in serialized output
        for security purposes.
        """
        data = self.serializer.data
        self.assertNotIn('password', data)

    def test_create_user_with_serializer(self):
        """
        Test the creation of a new user through the serializer.
        Verifies that:
        - All fields are correctly saved
        - Password is properly hashed
        - User is successfully created in the database
        """
        new_user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123'
        }
        serializer = UserSerializer(data=new_user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        # Verify all fields were saved correctly
        self.assertEqual(user.username, new_user_data['username'])
        self.assertEqual(user.email, new_user_data['email'])
        self.assertEqual(user.first_name, new_user_data['first_name'])
        self.assertEqual(user.last_name, new_user_data['last_name'])
        # Verify password was properly hashed
        self.assertTrue(user.check_password(new_user_data['password']))

    def test_update_user_with_serializer(self):
        """
        Test updating an existing user through the serializer.
        Verifies that partial updates work correctly.
        """
        updated_data = {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast'
        }
        serializer = UserSerializer(instance=self.user, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        # Verify fields were updated correctly
        self.assertEqual(updated_user.first_name, updated_data['first_name'])
        self.assertEqual(updated_user.last_name, updated_data['last_name'])

    def test_serializer_with_invalid_data(self):
        """
        Test serializer validation with invalid data.
        Verifies that appropriate error messages are generated.
        """
        invalid_data = {
            'username': '',  # Empty username should be invalid
            'email': 'invalid-email',  # Invalid email format
        }
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('email', serializer.errors)

    def test_password_validation(self):
        """
        Test password validation rules.
        Verifies that weak passwords are rejected according to Django's
        password validation rules.
        """
        weak_passwords = [
            {'password': '123'},  # Too short
            {'password': 'password'},  # Too common
            {'password': '12345678'},  # Numeric only
        ]
        for data in weak_passwords:
            # Create serializer with weak password
            serializer = UserSerializer(data={**self.user_attributes, **data})
            self.assertFalse(serializer.is_valid())
            self.assertIn('password', serializer.errors)

    def test_update_without_password(self):
        """
        Test user updates without changing password.
        Verifies that:
        - Updates work without providing password
        - Existing password remains unchanged
        """
        update_data = {
            'first_name': 'NewFirst',
            'email': 'newemail@example.com'
        }
        serializer = UserSerializer(instance=self.user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        # Verify fields were updated
        self.assertEqual(updated_user.first_name, update_data['first_name'])
        self.assertEqual(updated_user.email, update_data['email'])
        # Verify password remains unchanged
        self.assertTrue(updated_user.check_password(self.user_attributes['password']))

    def test_required_fields_on_create(self):
        """
        Test required field validation during user creation.
        Verifies that all required fields must be provided.
        """
        incomplete_data = {
            'username': 'newuser',
            'email': 'new@example.com'
            # Missing password and other required fields
        }
        serializer = UserSerializer(data=incomplete_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_read_only_fields(self):
        """
        Test protection of read-only fields.
        Verifies that read-only fields (like 'id') cannot be modified
        through the serializer.
        """
        data = {
            'id': 999,  # Attempting to modify read-only field
            'username': 'newusername'
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        
        # Verify id wasn't modified
        self.assertNotEqual(updated_user.id, data['id'])