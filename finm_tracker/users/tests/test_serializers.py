from django.test import TestCase
from django.contrib.auth import get_user_model
from ..serializers import UserSerializer

User = get_user_model()

class UserSerializerTest(TestCase):
    def setUp(self):
        self.user_attributes = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_attributes)
        self.serializer = UserSerializer(instance=self.user)

    def test_contains_expected_fields(self):
        data = self.serializer.data
        self.assertEqual(set(data.keys()), set(['id', 'username', 'email', 'first_name', 'last_name']))

    def test_username_field_content(self):
        data = self.serializer.data
        self.assertEqual(data['username'], self.user_attributes['username'])

    def test_email_field_content(self):
        data = self.serializer.data
        self.assertEqual(data['email'], self.user_attributes['email'])

    def test_first_name_field_content(self):
        data = self.serializer.data
        self.assertEqual(data['first_name'], self.user_attributes['first_name'])

    def test_last_name_field_content(self):
        data = self.serializer.data
        self.assertEqual(data['last_name'], self.user_attributes['last_name'])

    def test_password_field_not_included(self):
        data = self.serializer.data
        self.assertNotIn('password', data)

    def test_create_user_with_serializer(self):
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
        self.assertEqual(user.username, new_user_data['username'])
        self.assertEqual(user.email, new_user_data['email'])
        self.assertEqual(user.first_name, new_user_data['first_name'])
        self.assertEqual(user.last_name, new_user_data['last_name'])
        self.assertTrue(user.check_password(new_user_data['password']))

    def test_update_user_with_serializer(self):
        updated_data = {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast'
        }
        serializer = UserSerializer(instance=self.user, data=updated_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.first_name, updated_data['first_name'])
        self.assertEqual(updated_user.last_name, updated_data['last_name'])

    def test_serializer_with_invalid_data(self):
        invalid_data = {
            'username': '',  # Empty username should be invalid
            'email': 'invalid-email',  # Invalid email format
        }
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('email', serializer.errors)