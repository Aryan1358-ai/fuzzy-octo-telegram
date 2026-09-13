"""
API integration tests for activity submission and DB persistence.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from assessment.models import AssessmentSession, ActivityResponse, DomainScore


class ActivitySubmissionAPITests(TestCase):
    """Test activity submission via the REST API."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apitest', password='testpass')
        self.client.login(username='apitest', password='testpass')

        # Start a session
        res = self.client.post('/api/session/start/')
        self.assertEqual(res.status_code, 201)
        self.session_id = res.data['session_id']

    def test_submit_activity_persists_response_data(self):
        """Activity submission saves raw response_data to DB."""
        payload = {
            'response_data': {
                'pin_order': [
                    {'panel': 'db_log', 'timestamp': 1200},
                    {'panel': 'network_tab', 'timestamp': 3400},
                ],
            },
            'duration_ms': 5000,
        }
        res = self.client.post('/api/activity/3/submit/', payload, format='json')
        self.assertEqual(res.status_code, 200)

        # Verify DB
        ar = ActivityResponse.objects.get(
            session_id=self.session_id,
            activity_number=3,
        )
        self.assertEqual(ar.response_data['pin_order'][0]['panel'], 'db_log')
        self.assertEqual(ar.duration_ms, 5000)

    def test_submit_activity_persists_behavioral_signals(self):
        """Activity submission calculates and persists behavioral_signals."""
        payload = {
            'response_data': {
                'pin_order': [
                    {'panel': 'db_log', 'timestamp': 1200},
                ],
            },
            'duration_ms': 3000,
        }
        res = self.client.post('/api/activity/3/submit/', payload, format='json')
        self.assertEqual(res.status_code, 200)

        ar = ActivityResponse.objects.get(
            session_id=self.session_id,
            activity_number=3,
        )
        # behavioral_signals should now be populated by the server
        self.assertIn('triggered_signals', ar.behavioral_signals)
        self.assertIn('db_log_first', ar.behavioral_signals['triggered_signals'])

    def test_submit_activity_does_not_leak_scores(self):
        """API response should NOT contain signals_triggered or score_deltas."""
        payload = {
            'response_data': {'pin_order': [{'panel': 'db_log'}]},
            'duration_ms': 3000,
        }
        res = self.client.post('/api/activity/3/submit/', payload, format='json')
        self.assertNotIn('signals_triggered', res.data)
        self.assertNotIn('score_deltas', res.data)

    def test_empty_signals_distinguishable(self):
        """No signal-triggering behavior produces empty list, not missing field."""
        payload = {
            'response_data': {'pin_order': [{'panel': 'unknown_panel'}]},
            'duration_ms': 2000,
        }
        res = self.client.post('/api/activity/3/submit/', payload, format='json')
        self.assertEqual(res.status_code, 200)

        ar = ActivityResponse.objects.get(
            session_id=self.session_id,
            activity_number=3,
        )
        self.assertIn('triggered_signals', ar.behavioral_signals)
        self.assertEqual(ar.behavioral_signals['triggered_signals'], [])

    def test_session_stage_advances_after_6_activities(self):
        """Completing 6 activities advances stage to thinking_styles."""
        for act_num in range(1, 7):
            payload = {
                'response_data': {'test': True},
                'duration_ms': 1000,
            }
            self.client.post(f'/api/activity/{act_num}/submit/', payload, format='json')

        session = AssessmentSession.objects.get(id=self.session_id)
        self.assertEqual(session.current_stage, 'thinking_styles')

    def test_invalid_activity_number_rejected(self):
        """Activity numbers outside 1-6 are rejected."""
        payload = {
            'response_data': {'test': True},
            'duration_ms': 1000,
        }
        res = self.client.post('/api/activity/7/submit/', payload, format='json')
        self.assertEqual(res.status_code, 400)

        res = self.client.post('/api/activity/0/submit/', payload, format='json')
        self.assertEqual(res.status_code, 400)

    def test_resubmit_activity_updates_not_duplicates(self):
        """Resubmitting an activity updates the existing record."""
        payload1 = {
            'response_data': {'pin_order': [{'panel': 'db_log'}]},
            'duration_ms': 3000,
        }
        self.client.post('/api/activity/3/submit/', payload1, format='json')

        payload2 = {
            'response_data': {'pin_order': [{'panel': 'frontend_render'}]},
            'duration_ms': 4000,
        }
        self.client.post('/api/activity/3/submit/', payload2, format='json')

        # Should be exactly 1 record, not 2
        count = ActivityResponse.objects.filter(
            session_id=self.session_id,
            activity_number=3,
        ).count()
        self.assertEqual(count, 1)

        ar = ActivityResponse.objects.get(
            session_id=self.session_id,
            activity_number=3,
        )
        # Should have the updated signals
        self.assertIn('frontend_render_first',
                      ar.behavioral_signals['triggered_signals'])

    def test_unauthenticated_rejected(self):
        """Unauthenticated requests are rejected."""
        client = APIClient()
        payload = {
            'response_data': {'test': True},
            'duration_ms': 1000,
        }
        res = client.post('/api/activity/1/submit/', payload, format='json')
        self.assertEqual(res.status_code, 403)
