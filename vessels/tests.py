from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from vessels.models import Vessel


class VesselModelTest(TestCase):
    """FR-VO-PROF-001: Vessel profile model validation"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='skipper',
            password='SecurePass123!'
        )

    def test_vessel_creation(self):
        """Vessel is created and saved correctly"""
        vessel = Vessel.objects.create(
            owner=self.user,
            name='MV Ambition',
            imo_number='IMO1234567',
            vessel_type='cargo',
            flag='United Kingdom',
        )
        self.assertEqual(vessel.name, 'MV Ambition')
        self.assertEqual(vessel.owner, self.user)

    def test_vessel_str_representation(self):
        """__str__ returns name and IMO number"""
        vessel = Vessel.objects.create(
            owner=self.user,
            name='MV Ambition',
            imo_number='IMO1234567',
            vessel_type='cargo',
            flag='United Kingdom',
        )
        self.assertIn('MV Ambition', str(vessel))
        self.assertIn('IMO1234567', str(vessel))

    def test_imo_number_unique(self):
        """Duplicate IMO number raises IntegrityError"""
        Vessel.objects.create(
            owner=self.user,
            name='First Vessel',
            imo_number='IMO9999999',
            vessel_type='tanker',
            flag='United Kingdom',
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Vessel.objects.create(
                owner=self.user,
                name='Second Vessel',
                imo_number='IMO9999999',
                vessel_type='fishing',
                flag='United Kingdom',
            )

    def test_multiple_vessels_per_user(self):
        """A user can own more than one vessel"""
        Vessel.objects.create(
            owner=self.user, name='Vessel One',
            imo_number='IMO0000001', vessel_type='cargo', flag='UK',
        )
        Vessel.objects.create(
            owner=self.user, name='Vessel Two',
            imo_number='IMO0000002', vessel_type='tanker', flag='UK',
        )
        self.assertEqual(Vessel.objects.filter(owner=self.user).count(), 2)

    def test_vessel_deleted_with_user(self):
        """Vessels cascade-delete when user is deleted"""
        Vessel.objects.create(
            owner=self.user, name='Doomed Vessel',
            imo_number='IMO0000003', vessel_type='tug', flag='UK',
        )
        self.user.delete()
        self.assertEqual(Vessel.objects.filter(imo_number='IMO0000003').count(), 0)


class VesselViewTest(TestCase):
    """FR-VO-PROF-001/002: Vessel CRUD views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='skipper',
            password='SecurePass123!'
        )
        self.other_user = User.objects.create_user(
            username='other',
            password='SecurePass123!'
        )
        self.client.login(username='skipper', password='SecurePass123!')
        self.vessel = Vessel.objects.create(
            owner=self.user,
            name='MV Ambition',
            imo_number='IMO1234567',
            vessel_type='cargo',
            flag='United Kingdom',
        )

    def test_vessel_list_loads(self):
        """Vessel list page returns 200 for authenticated user"""
        response = self.client.get(reverse('vessels:vessel_list'))
        self.assertEqual(response.status_code, 200)

    def test_vessel_list_shows_own_vessels_only(self):
        """User only sees their own vessels"""
        Vessel.objects.create(
            owner=self.other_user,
            name='Other Vessel',
            imo_number='IMO9998887',
            vessel_type='fishing',
            flag='France',
        )
        response = self.client.get(reverse('vessels:vessel_list'))
        self.assertContains(response, 'MV Ambition')
        self.assertNotContains(response, 'Other Vessel')

    def test_add_vessel_get(self):
        """Add vessel page loads for authenticated user"""
        response = self.client.get(reverse('vessels:vessel_add'))
        self.assertEqual(response.status_code, 200)

    def test_add_vessel_post_valid(self):
        """Valid vessel form creates a new vessel"""
        self.client.post(reverse('vessels:vessel_add'), {
            'name': 'New Vessel',
            'imo_number': 'IMO7654321',
            'vessel_type': 'fishing',
            'flag': 'United Kingdom',
        })
        self.assertTrue(Vessel.objects.filter(imo_number='IMO7654321').exists())

    def test_vessel_detail_loads(self):
        """Vessel detail page returns 200"""
        response = self.client.get(reverse('vessels:vessel_detail', args=[self.vessel.pk]))
        self.assertEqual(response.status_code, 200)

    def test_vessel_detail_other_user_blocked(self):
        """User cannot view another user's vessel detail"""
        self.client.login(username='other', password='SecurePass123!')
        response = self.client.get(reverse('vessels:vessel_detail', args=[self.vessel.pk]))
        self.assertEqual(response.status_code, 404)

    def test_delete_vessel(self):
        """Vessel can be deleted by its owner"""
        self.client.post(reverse('vessels:vessel_delete', args=[self.vessel.pk]))
        self.assertFalse(Vessel.objects.filter(pk=self.vessel.pk).exists())