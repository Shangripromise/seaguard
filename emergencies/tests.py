from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from vessels.models import Vessel
from emergencies.models import EmergencyRequest


class EmergencyRequestModelTest(TestCase):
    """FR-VO-REQ-001/007: Emergency request model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='skipper',
            password='SecurePass123!'
        )
        self.vessel = Vessel.objects.create(
            owner=self.user,
            name='MV Ambition',
            imo_number='IMO1234567',
            vessel_type='cargo',
            flag='United Kingdom',
        )

    def test_emergency_request_creation(self):
        """Emergency request is created with correct fields"""
        req = EmergencyRequest.objects.create(
            vessel=self.vessel,
            submitted_by=self.user,
            emergency_type='fire',
            description='Engine room fire',
            latitude=51.5074,
            longitude=-3.1791,
        )
        self.assertEqual(req.status, 'active')
        self.assertEqual(req.submitted_by, self.user)
        self.assertEqual(req.vessel, self.vessel)

    def test_emergency_request_default_status_active(self):
        """New emergency request defaults to active status"""
        req = EmergencyRequest.objects.create(
            vessel=self.vessel,
            submitted_by=self.user,
            emergency_type='flooding',
            description='Taking on water',
        )
        self.assertEqual(req.status, 'active')

    def test_emergency_request_str(self):
        """__str__ includes emergency type and vessel name"""
        req = EmergencyRequest.objects.create(
            vessel=self.vessel,
            submitted_by=self.user,
            emergency_type='fire',
            description='fire on deck',
        )
        self.assertIn('fire', str(req).lower())

    def test_status_can_be_resolved(self):
        """Emergency status can be updated to resolved"""
        req = EmergencyRequest.objects.create(
            vessel=self.vessel,
            submitted_by=self.user,
            emergency_type='grounding',
            description='Run aground on sandbar',
        )
        req.status = 'resolved'
        req.save()
        updated = EmergencyRequest.objects.get(pk=req.pk)
        self.assertEqual(updated.status, 'resolved')

    def test_emergency_deleted_with_vessel(self):
        """Emergency requests cascade-delete when vessel is deleted"""
        req = EmergencyRequest.objects.create(
            vessel=self.vessel,
            submitted_by=self.user,
            emergency_type='collision',
            description='Collision with debris',
        )
        self.vessel.delete()
        self.assertFalse(EmergencyRequest.objects.filter(pk=req.pk).exists())

    def test_optional_gps_fields(self):
        """GPS coordinates are optional — request saves without them"""
        req = EmergencyRequest.objects.create(
            vessel=self.vessel,
            submitted_by=self.user,
            emergency_type='medical',
            description='Crew member injured',
        )
        self.assertIsNone(req.latitude)
        self.assertIsNone(req.longitude)

    def test_multiple_requests_per_user(self):
        """A user can have multiple emergency requests"""
        for i in range(3):
            EmergencyRequest.objects.create(
                vessel=self.vessel,
                submitted_by=self.user,
                emergency_type='other',
                description=f'Incident {i}',
            )
        self.assertEqual(
            EmergencyRequest.objects.filter(submitted_by=self.user).count(), 3
        )


class EmergencyRequestViewTest(TestCase):
    """FR-VO-REQ-001/007: Emergency request views"""

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
        self.emergency = EmergencyRequest.objects.create(
            vessel=self.vessel,
            submitted_by=self.user,
            emergency_type='fire',
            description='Engine fire',
        )

    def test_emergency_list_loads(self):
        """Emergency list page returns 200"""
        response = self.client.get(reverse('emergency_list'))
        self.assertEqual(response.status_code, 200)

    def test_emergency_list_shows_own_requests_only(self):
        """User sees only their own emergency requests"""
        other_vessel = Vessel.objects.create(
            owner=self.other_user,
            name='Other Vessel',
            imo_number='IMO9998887',
            vessel_type='fishing',
            flag='France',
        )
        EmergencyRequest.objects.create(
            vessel=other_vessel,
            submitted_by=self.other_user,
            emergency_type='flooding',
            description='Other user flooding',
        )
        response = self.client.get(reverse('emergency_list'))
        self.assertContains(response, 'MV Ambition')
        self.assertNotContains(response, 'Other user flooding')

    def test_submit_emergency_get(self):
        """Submit emergency page loads for authenticated user"""
        response = self.client.get(reverse('emergency_submit'))
        self.assertEqual(response.status_code, 200)

    def test_submit_emergency_post_valid(self):
        """Valid emergency form creates a new request"""
        response = self.client.post(reverse('emergency_submit'), {
            'vessel': self.vessel.pk,
            'emergency_type': 'flooding',
            'description': 'Water ingress in engine room',
            'latitude': '',
            'longitude': '',
        })
        self.assertTrue(
            EmergencyRequest.objects.filter(description='Water ingress in engine room').exists()
        )

    def test_submit_emergency_sets_submitted_by(self):
        """Submitted emergency is linked to the logged-in user"""
        self.client.post(reverse('emergency_submit'), {
            'vessel': self.vessel.pk,
            'emergency_type': 'grounding',
            'description': 'Run aground near harbour',
            'latitude': '',
            'longitude': '',
        })
        req = EmergencyRequest.objects.get(description='Run aground near harbour')
        self.assertEqual(req.submitted_by, self.user)

    def test_emergency_detail_loads(self):
        """Emergency detail page returns 200 for owner"""
        response = self.client.get(
            reverse('emergency_detail', args=[self.emergency.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_emergency_detail_other_user_blocked(self):
        """User cannot view another user's emergency detail"""
        self.client.login(username='other', password='SecurePass123!')
        response = self.client.get(
            reverse('emergency_detail', args=[self.emergency.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_submit_redirects(self):
        """Unauthenticated user cannot submit emergency"""
        self.client.logout()
        response = self.client.get(reverse('emergency_submit'))
        self.assertEqual(response.status_code, 302)
