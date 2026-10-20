from django.test import TestCase, Client
from django.urls import reverse
from users.models import User


class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='john',
            password='password123',
            email='john@example.com',
            first_name='John',
            last_name='Doe'
        )

    def test_dashboard_redirects_unauthenticated_user(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('users:login')))

    def test_dashboard_authenticated_user_access(self):
        self.client.login(username='john', password='password123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome back! John')
        # Kept cards
        self.assertContains(response, 'Events')
        self.assertContains(response, '696')
        self.assertContains(response, 'Reports')
        self.assertContains(response, '59')
        self.assertContains(response, 'Employees')
        self.assertContains(response, '96')
        # Removed cards should NOT be present
        self.assertNotContains(response, 'Payroll')
        self.assertNotContains(response, 'Clients')
        self.assertNotContains(response, 'Projects')
        # Removed sidebar menus should NOT be present
        self.assertNotContains(response, 'eCommerce')
        self.assertNotContains(response, "Haven't")
        # Charts
        self.assertContains(response, 'Revenue Updates')
        self.assertContains(response, 'Yearly Breakup')
        self.assertContains(response, '$36,358')
