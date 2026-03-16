from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class UserRegistrationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')

    def test_register_page_loads(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)

    def test_register_valid_user(self):
        self.client.post(self.register_url, {
            'username': 'testuser',
            'first_name': 'John',
            'last_name': 'Davies',
            'email': 'test@seaguard.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_register_duplicate_username_fails(self):
        User.objects.create_user(username='existing', password='pass12345!')
        self.client.post(self.register_url, {
            'username': 'existing',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'new@seaguard.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertEqual(User.objects.filter(username='existing').count(), 1)

    def test_register_password_mismatch_fails(self):
        self.client.post(self.register_url, {
            'username': 'newuser',
            'first_name': 'Bob',
            'last_name': 'Jones',
            'email': 'new@seaguard.com',
            'password1': 'SecurePass123!',
            'password2': 'WrongPassword!',
        })
        self.assertFalse(User.objects.filter(username='newuser').exists())


class UserLoginTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='testuser',
            password='SecurePass123!'
        )

    def test_login_page_loads(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

    def test_login_valid_credentials(self):
        self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'SecurePass123!',
        })
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_invalid_password_fails(self):
        self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword!',
        })
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_nonexistent_user_fails(self):
        self.client.post(self.login_url, {
            'username': 'nobody',
            'password': 'SecurePass123!',
        })
        self.assertNotIn('_auth_user_id', self.client.session)


class UserLogoutTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='SecurePass123!'
        )
        self.client.login(username='testuser', password='SecurePass123!')

    def test_logout_clears_session(self):
        self.client.get(reverse('logout'))
        self.assertNotIn('_auth_user_id', self.client.session)


class UnauthenticatedAccessTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('dashboard')}"
        )

    def test_vessel_list_requires_login(self):
        response = self.client.get(reverse('vessel_list'))
        self.assertEqual(response.status_code, 302)

    def test_emergency_list_requires_login(self):
        response = self.client.get(reverse('emergency_list'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_requires_staff(self):
        user = User.objects.create_user(username='regular', password='pass12345!')
        self.client.login(username='regular', password='pass12345!')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertNotEqual(response.status_code, 200)