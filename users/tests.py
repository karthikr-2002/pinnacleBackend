from django.test import TestCase, Client
from django.urls import reverse
from users.models import User


class UserAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='Password123!',
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            role='manager'
        )

    def test_user_properties(self):
        self.assertEqual(self.user.display_name, 'Test User')
        self.assertEqual(self.user.role, 'manager')
        self.assertEqual(str(self.user), 'testuser')

    def test_login_page_renders(self):
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tailwindadmin')
        self.assertContains(response, 'Welcome back!')

    def test_login_success(self):
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'Password123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard:index'))

    def test_login_failure(self):
        response = self.client.post(reverse('users:login'), {
            'username': 'testuser',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_logout(self):
        self.client.login(username='testuser', password='Password123!')
        response = self.client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:login'))

    def test_register_page_renders(self):
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create your account')

    def test_register_success(self):
        response = self.client.post(reverse('users:register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'Person',
            'email': 'new@example.com',
            'role': 'user',
            'password1': 'SecretPass999!',
            'password2': 'SecretPass999!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
