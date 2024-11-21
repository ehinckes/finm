from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

class UserViewSetTestCase(APITestCase):
    """
    Test suite for UserViewSet functionality.
    Tests CRUD operations, custom endpoints, permissions, and edge cases.
    """
    
    def setUp(self):
        """
        Initialize test data and authenticate the test client.
        Creates a test user and sets up authentication for subsequent requests.
        """
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        # Create a test user and authenticate the client
        self.user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=self.user)

    def test_register_user(self):
        """
        Test user registration functionality.
        Verifies that a new user can be created with valid data.
        Checks response status, user count, and returned data format.
        """
        url = reverse('user-register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['email'], 'newuser@example.com')
        # Verify password is not exposed in response
        self.assertNotIn('password', response.data)

    def test_me_endpoint(self):
        """
        Test the custom /me endpoint.
        Verifies that authenticated users can retrieve their own data.
        """
        url = reverse('user-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['email'], self.user.email)

    def test_list_users(self):
        """
        Test the user listing endpoint.
        Verifies that users can only see their own data in the list view.
        """
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only the authenticated user should be returned
        self.assertEqual(response.data[0]['username'], self.user.username)

    def test_retrieve_user(self):
        """
        Test user detail retrieval.
        Verifies that users can access their detailed information.
        """
        url = reverse('user-detail', kwargs={'pk': self.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)

    def test_update_user(self):
        """
        Test user update functionality.
        Verifies that users can update their profile information.
        """
        url = reverse('user-detail', kwargs={'pk': self.user.pk})
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')

    def test_delete_user(self):
        """
        Test user deletion.
        Verifies that users can delete their account.
        """
        url = reverse('user-detail', kwargs={'pk': self.user.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)

    def test_register_user_invalid_data(self):
        """
        Test user registration with invalid data.
        Verifies that appropriate error responses are returned for invalid input.
        """
        url = reverse('user-register')
        data = {
            'username': 'newuser',
            'email': 'invalid_email',
            'password': 'short'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)

    def test_unauthenticated_access(self):
        """
        Test access attempts without authentication.
        Verifies that unauthenticated users cannot access protected endpoints.
        """
        self.client.force_authenticate(user=None)
        urls = [
            reverse('user-list'),
            reverse('user-me'),
            reverse('user-detail', kwargs={'pk': self.user.pk})
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_modify_other_user(self):
        """
        Test user permission boundaries.
        Verifies that users cannot modify other users' data.
        """
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='password123'
        )
        url = reverse('user-detail', kwargs={'pk': other_user.pk})
        response = self.client.patch(url, {'first_name': 'Hacked'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_username_registration(self):
        """
        Test duplicate username handling.
        Verifies that users cannot register with an existing username.
        """
        url = reverse('user-register')
        data = self.user_data.copy()
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_password_is_properly_hashed(self):
        """
        Test password security.
        Verifies that passwords are properly hashed before storage.
        """
        url = reverse('user-register')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        new_user = User.objects.get(username='newuser')
        self.assertTrue(new_user.check_password('testpass123'))
        self.assertNotEqual(new_user.password, 'testpass123')