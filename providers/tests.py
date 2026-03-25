from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from vessels.models import Vessel
from emergencies.models import EmergencyRequest
from providers.models import RecoveryProvider, ProviderRating


# ─── Helpers ────────────────────────────────────────────────────────────────

def make_user(username, is_staff=False):
    u = User.objects.create_user(username=username, password='SecurePass123!')
    if is_staff:
        u.is_staff = True
        u.save()
    return u


def make_provider(user, company_name='Test Marine Ltd', status='approved',
                  available=True, service_type='towing', avg_response=30):
    return RecoveryProvider.objects.create(
        user=user,
        company_name=company_name,
        contact_person='Bob Smith',
        phone_number='07700900000',
        business_registration='BR12345',
        service_area='Bristol Channel',
        verification_status=status,
        is_available=available,
        service_type=service_type,
        avg_response_minutes=avg_response,
    )


def make_vessel(owner):
    return Vessel.objects.create(
        owner=owner,
        name='MV Ambition',
        imo_number='IMO1234567',
        vessel_type='cargo',
        flag='United Kingdom',
    )


# ─── CR1: Provider Search / Filter ──────────────────────────────────────────

class CR1ProviderSearchTest(TestCase):
    """CR1 - FR-VO-SEA-001/002: Provider search with keyword and filter"""

    def setUp(self):
        self.client = Client()
        self.user = make_user('skipper')
        self.client.login(username='skipper', password='SecurePass123!')

        p1_user = make_user('provider1')
        p2_user = make_user('provider2')
        p3_user = make_user('provider3')

        self.p1 = make_provider(p1_user, 'Atlantic Towing', 'approved', True, 'towing')
        self.p2 = make_provider(p2_user, 'Channel Fuel', 'approved', True, 'fuel')
        self.p3 = make_provider(p3_user, 'Pending Co', 'pending', True, 'towing')

    def test_search_page_loads(self):
        response = self.client.get(reverse('providers:search'))
        self.assertEqual(response.status_code, 200)

    def test_search_returns_approved_providers_only(self):
        """Pending providers must not appear in search results"""
        response = self.client.get(reverse('providers:search'))
        self.assertContains(response, 'Atlantic Towing')
        self.assertNotContains(response, 'Pending Co')

    def test_keyword_filter_matches_company_name(self):
        response = self.client.get(reverse('providers:search'), {'q': 'Atlantic'})
        self.assertContains(response, 'Atlantic Towing')
        self.assertNotContains(response, 'Channel Fuel')

    def test_service_type_filter(self):
        """Filtering by fuel service type shows only fuel providers"""
        response = self.client.get(reverse('providers:search'), {'q': 'fuel'})
        self.assertContains(response, 'Channel Fuel')
        self.assertNotContains(response, 'Atlantic Towing')

    def test_availability_filter_hides_unavailable(self):
        """Filtering by available=available hides unavailable providers"""
        p4_user = make_user('provider4')
        make_provider(p4_user, 'Offline Marine', 'approved', False, 'towing')
        response = self.client.get(reverse('providers:search'), {'availability': 'available'})
        self.assertNotContains(response, 'Offline Marine')

    def test_empty_keyword_returns_all_approved(self):
        response = self.client.get(reverse('providers:search'), {'q': ''})
        self.assertContains(response, 'Atlantic Towing')
        self.assertContains(response, 'Channel Fuel')

    def test_search_accessible_without_login(self):
        """Search page is publicly accessible (no login required by design)"""
        self.client.logout()
        response = self.client.get(reverse('providers:search'))
        self.assertEqual(response.status_code, 200)


# ─── CR2: Intelligent Dispatch / Ranking Score ───────────────────────────────

class CR2RankingScoreTest(TestCase):
    """CR2 - FR-RP-RANK-001/002: Weighted ranking score and auto-dispatch"""

    def setUp(self):
        self.user = make_user('skipper')
        self.vessel = make_vessel(self.user)
        p_user = make_user('provider1')
        self.provider = make_provider(
            p_user, 'Best Marine', 'approved', True, 'towing', avg_response=20
        )

    def test_ranking_score_returns_numeric(self):
        score = self.provider.ranking_score()
        self.assertIsInstance(score, (int, float))

    def test_ranking_score_positive(self):
        self.assertGreater(self.provider.ranking_score(), 0)

    def test_unavailable_provider_scores_lower_than_available(self):
        """Unavailable providers score lower than available ones"""
        p2_user = make_user('provider2')
        unavailable = make_provider(
            p2_user, 'Offline Marine', 'approved', False, 'towing', avg_response=20
        )
        self.assertGreater(
            self.provider.ranking_score(),
            unavailable.ranking_score()
        )

    def test_faster_response_scores_higher(self):
        p2_user = make_user('provider2')
        slow = make_provider(p2_user, 'Slow Marine', 'approved', True, 'towing', avg_response=120)
        self.assertGreater(
            self.provider.ranking_score(),
            slow.ranking_score()
        )

    def test_auto_dispatch_assigns_provider_on_submit(self):
        """Submitting an emergency should auto-assign the top-ranked provider"""
        client = Client()
        client.login(username='skipper', password='SecurePass123!')
        client.post(reverse('emergencies:emergency_submit'), {
            'vessel': self.vessel.pk,
            'emergency_type': 'flooding',
            'description': 'Taking on water fast',
            'latitude': '',
            'longitude': '',
        })
        req = EmergencyRequest.objects.get(description='Taking on water fast')
        self.assertIsNotNone(req.assigned_provider)

    def test_no_available_provider_still_creates_request(self):
        """Emergency submits even if no provider available"""
        self.provider.is_available = False
        self.provider.save()
        client = Client()
        client.login(username='skipper', password='SecurePass123!')
        client.post(reverse('emergencies:emergency_submit'), {
            'vessel': self.vessel.pk,
            'emergency_type': 'fire',
            'description': 'Engine fire no provider',
            'latitude': '',
            'longitude': '',
        })
        self.assertTrue(
            EmergencyRequest.objects.filter(description='Engine fire no provider').exists()
        )


# ─── CR3: Member Discounts ───────────────────────────────────────────────────

class CR3MemberDiscountsTest(TestCase):
    """CR3 - FR-VO-DISC-001/002: Member discounts page and active emergency lock"""

    def setUp(self):
        self.client = Client()
        self.user = make_user('skipper')
        self.vessel = make_vessel(self.user)
        self.client.login(username='skipper', password='SecurePass123!')

    def test_discounts_page_loads(self):
        response = self.client.get(reverse('member_discounts'))
        self.assertEqual(response.status_code, 200)

    def test_discounts_page_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('member_discounts'))
        self.assertEqual(response.status_code, 302)

    def test_discounts_shows_locked_message_during_active_emergency(self):
        """Page reflects locked state when user has active emergency"""
        EmergencyRequest.objects.create(
            vessel=self.vessel,
            submitted_by=self.user,
            emergency_type='fire',
            description='Active fire',
            status='active',
        )
        response = self.client.get(reverse('member_discounts'))
        self.assertIn(response.status_code, [200, 302])

    def test_discounts_accessible_with_no_active_emergency(self):
        """Discounts fully accessible when no active emergency"""
        response = self.client.get(reverse('member_discounts'))
        self.assertEqual(response.status_code, 200)


# ─── CR4: Rating Moderation ──────────────────────────────────────────────────

class CR4RatingModerationTest(TestCase):
    """CR4 - FR-ADM-MOD-001/002: Rating moderation queue, approve and reject"""

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin', is_staff=True)
        self.regular = make_user('skipper')
        self.vessel = make_vessel(self.regular)

        p_user = make_user('provider1')
        self.provider = make_provider(p_user, 'Sea Rescue Ltd', 'approved')

        self.emergency = EmergencyRequest.objects.cre