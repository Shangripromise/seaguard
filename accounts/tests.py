from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import datetime

from .models import Voucher, VoucherRedemption


class UserRegistrationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')

    def test_register_page_loads(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)

    def test_register_valid_user(self):
        self.client.post(self.register_url, {
            'username':   'testuser',
            'first_name': 'John',
            'last_name':  'Davies',
            'email':      'test@seaguard.com',
            'password1':  'SecurePass123!',
            'password2':  'SecurePass123!',
        })
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_register_duplicate_username_fails(self):
        User.objects.create_user(username='existing', password='pass12345!')
        self.client.post(self.register_url, {
            'username':   'existing',
            'first_name': 'Jane',
            'last_name':  'Smith',
            'email':      'new@seaguard.com',
            'password1':  'SecurePass123!',
            'password2':  'SecurePass123!',
        })
        self.assertEqual(User.objects.filter(username='existing').count(), 1)

    def test_register_password_mismatch_fails(self):
        self.client.post(self.register_url, {
            'username':   'newuser',
            'first_name': 'Bob',
            'last_name':  'Jones',
            'email':      'new@seaguard.com',
            'password1':  'SecurePass123!',
            'password2':  'WrongPassword!',
        })
        self.assertFalse(User.objects.filter(username='newuser').exists())


class UserLoginTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
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
        self.client.get(reverse('accounts:logout'))
        self.assertNotIn('_auth_user_id', self.client.session)


class UnauthenticatedAccessTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}"
        )

    def test_vessel_list_requires_login(self):
        response = self.client.get(reverse('vessels:vessel_list'))
        self.assertEqual(response.status_code, 302)

    def test_emergency_list_requires_login(self):
        response = self.client.get(reverse('emergencies:emergency_list'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_requires_staff(self):
        user = User.objects.create_user(username='regular', password='pass12345!')
        self.client.login(username='regular', password='pass12345!')
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertNotEqual(response.status_code, 200)


# ── CR6: Voucher Service Tests ────────────────────────────────────────────────

class VoucherModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='voucheruser', password='testpass123'
        )
        self.voucher = Voucher.objects.create(
            code='TEST10',
            discount_type='percentage',
            discount_value=10,
            applies_to='general',
            is_active=True,
        )

    def test_valid_voucher_is_valid(self):
        """Active voucher with no expiry and no max uses is valid."""
        valid, reason = self.voucher.is_valid()
        self.assertTrue(valid)
        self.assertIsNone(reason)

    def test_inactive_voucher_is_invalid(self):
        """Inactive voucher is rejected."""
        self.voucher.is_active = False
        self.voucher.save()
        valid, reason = self.voucher.is_valid()
        self.assertFalse(valid)
        self.assertEqual(reason, 'This voucher is no longer active.')

    def test_expired_voucher_is_invalid(self):
        """Voucher with past expiry date is rejected."""
        self.voucher.expiry_date = datetime.date(2000, 1, 1)
        self.voucher.save()
        valid, reason = self.voucher.is_valid()
        self.assertFalse(valid)
        self.assertEqual(reason, 'This voucher has expired.')

    def test_max_uses_exceeded_is_invalid(self):
        """Voucher that has hit max uses is rejected."""
        self.voucher.max_uses = 1
        self.voucher.save()
        VoucherRedemption.objects.create(
            voucher=self.voucher,
            redeemed_by=self.user,
            applied_to='general',
        )
        valid, reason = self.voucher.is_valid()
        self.assertFalse(valid)
        self.assertEqual(reason, 'This voucher has reached its maximum number of uses.')

    def test_times_used_count(self):
        """times_used() returns correct redemption count."""
        self.assertEqual(self.voucher.times_used(), 0)
        VoucherRedemption.objects.create(
            voucher=self.voucher,
            redeemed_by=self.user,
            applied_to='general',
        )
        self.assertEqual(self.voucher.times_used(), 1)


class VoucherRedemptionViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='redeemuser', password='testpass123'
        )
        self.admin = User.objects.create_user(
            username='adminuser', password='testpass123', is_staff=True
        )
        self.voucher = Voucher.objects.create(
            code='REDEEM10',
            discount_type='percentage',
            discount_value=10,
            applies_to='general',
            is_active=True,
        )

    def test_redeem_page_requires_login(self):
        """Unauthenticated user is redirected to login."""
        response = self.client.get(reverse('accounts:redeem_voucher'))
        self.assertNotEqual(response.status_code, 200)

    def test_valid_redemption_creates_record(self):
        """Valid code creates a VoucherRedemption record."""
        self.client.login(username='redeemuser', password='testpass123')
        self.client.post(reverse('accounts:redeem_voucher'), {'code': 'REDEEM10'})
        self.assertEqual(
            VoucherRedemption.objects.filter(
                voucher=self.voucher, redeemed_by=self.user
            ).count(), 1
        )

    def test_nonexistent_code_shows_error(self):
        """Non-existent code shows error, no record created."""
        self.client.login(username='redeemuser', password='testpass123')
        self.client.post(reverse('accounts:redeem_voucher'), {'code': 'FAKECODE'})
        self.assertEqual(VoucherRedemption.objects.count(), 0)

    def test_double_redemption_blocked(self):
        """Same member cannot redeem same voucher twice."""
        self.client.login(username='redeemuser', password='testpass123')
        self.client.post(reverse('accounts:redeem_voucher'), {'code': 'REDEEM10'})
        self.client.post(reverse('accounts:redeem_voucher'), {'code': 'REDEEM10'})
        self.assertEqual(VoucherRedemption.objects.count(), 1)

    def test_admin_voucher_list_blocked_for_regular_user(self):
        """Regular user cannot access admin voucher list."""
        self.client.login(username='redeemuser', password='testpass123')
        response = self.client.get(reverse('accounts:admin_voucher_list'))
        self.assertNotEqual(response.status_code, 200)

    def test_admin_voucher_list_accessible_for_staff(self):
        """Staff user can access admin voucher list."""
        self.client.login(username='adminuser', password='testpass123')
        response = self.client.get(reverse('accounts:admin_voucher_list'))
        self.assertEqual(response.status_code, 200)