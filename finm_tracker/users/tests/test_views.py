from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

class UserViewSetTestCase(APITestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=self.user)

    def test_register_user(self):
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
        self.assertNotIn('password', response.data)

    def test_me_endpoint(self):
        url = reverse('user-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['email'], self.user.email)

    def test_list_users(self):
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only the authenticated user should be returned
        self.assertEqual(response.data[0]['username'], self.user.username)

    def test_retrieve_user(self):
        url = reverse('user-detail', kwargs={'pk': self.user.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)

    def test_update_user(self):
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
        url = reverse('user-detail', kwargs={'pk': self.user.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)

    def test_register_user_invalid_data(self):
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