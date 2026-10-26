import base64

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from evaluations.models import Unit

TINY_PNG = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
)


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


class EmployeeAdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@care.com',
            password='Password123!',
            role='admin',
        )
        self.unit = Unit.objects.create(name='Sunrise Wing', place='Building A')
        self.staff = User.objects.create_user(
            username='nurse_sarah',
            password='Password123!',
            role='user',
        )

    def test_staff_cannot_open_employee_pages(self):
        self.client.login(username='nurse_sarah', password='Password123!')
        response = self.client.get(reverse('employees:list'))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_employee_with_unit(self):
        self.client.login(username='admin', password='Password123!')
        photo = SimpleUploadedFile('avatar.png', TINY_PNG, content_type='image/png')
        response = self.client.post(reverse('employees:create'), {
            'full_name': 'Maria Garcia',
            'employee_id': 'EMP-2044',
            'email': 'maria.garcia@care.com',
            'password': 'SecretPass999!',
            'phone': '+1 555 0199',
            'unit': self.unit.id,
            'photo': photo,
        })
        self.assertEqual(response.status_code, 302)
        employee = User.objects.get(employee_id='EMP-2044')
        self.assertEqual(employee.username, 'EMP-2044')
        self.assertEqual(employee.first_name, 'Maria')
        self.assertEqual(employee.last_name, 'Garcia')
        self.assertEqual(employee.phone, '+1 555 0199')
        self.assertTrue(self.unit.users.filter(id=employee.id).exists())
