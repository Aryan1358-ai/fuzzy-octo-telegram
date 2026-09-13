"""
Unit tests for the scoring pipeline, context modifiers, and validation multipliers.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from assessment.models import AssessmentSession, ActivityResponse, DomainScore
from assessment.scoring import (
    calculate_activity_scores,
    calculate_pre_assessment_scores,
    _apply_context_modifiers,
    apply_validation_multipliers,
    SIGNAL_EXTRACTORS,
)
from assessment.signals_config import DOMAINS


class FullPipelineTests(TestCase):
    """Test the full scoring pipeline across all 6 activities."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.session = AssessmentSession.objects.create(user=self.user)

    def _create_activity(self, number, response_data):
        return ActivityResponse.objects.create(
            session=self.session,
            activity_number=number,
            response_data=response_data,
            duration_ms=5000,
        )

    def test_full_pipeline_all_signals(self):
        """A user triggering signals across all 6 activities gets aggregate scores."""
        # Activity 1: correct full flow
        self._create_activity(1, {
            'placement_order': [
                {'label': 'API Gateway'},
                {'label': 'Database'},
                {'label': 'User Request'},
            ],
            'final_positions': [
                {'label': 'User Request'},
                {'label': 'API Gateway'},
                {'label': 'Application Server'},
                {'label': 'Database'},
                {'label': 'ML Model'},
                {'label': 'UI Response'},
            ],
        })
        # Activity 2: good form layout
        self._create_activity(2, {
            'final_positions': [
                {'label': 'Page Title'},
                {'label': 'Email'},
                {'label': 'Error Message'},
                {'label': 'Password'},
                {'label': 'Submit Button'},
            ],
            'timing': {'error_message_ms': 6000},
        })
        # Activity 3: db_log first
        self._create_activity(3, {
            'pin_order': [{'panel': 'db_log'}, {'panel': 'network_tab'}],
        })
        # Activity 4: balanced architecture
        self._create_activity(4, {
            'selection_order': [
                {'tile': 'Load Balancer'},
                {'tile': 'Monitoring'},
                {'tile': 'Database'},
                {'tile': 'Redis'},
                {'tile': 'Firewall'},
            ],
        })
        # Activity 5: all vulnerabilities
        self._create_activity(5, {
            'flag_order': [
                {'vulnerability': 'session_token_url'},
                {'vulnerability': 'plain_text_password'},
                {'vulnerability': 'no_rate_limit'},
                {'vulnerability': 'missing_captcha'},
            ],
            'time_to_first_flag_ms': 5000,
        })
        # Activity 6: product-minded
        self._create_activity(6, {
            'categories': {
                'ship': ['2FA', 'Dark Mode'],
                'reconsider': ['In-App Notifications'],
                'cut': ['Profile Badges'],
            },
        })

        domain_score, all_signals = calculate_pre_assessment_scores(self.session)

        # All 6 activities should have signals
        self.assertEqual(len(all_signals), 6)
        for act_num in range(1, 7):
            self.assertIn(act_num, all_signals)
            self.assertIsInstance(all_signals[act_num], list)

        # Domain scores should be non-zero for active domains
        scores = domain_score.as_dict()
        self.assertGreater(scores['backend'], 0)
        self.assertGreater(scores['cybersecurity'], 0)
        self.assertGreater(scores['frontend'], 0)

    def test_empty_activities_zero_scores(self):
        """No activities = all zero scores."""
        domain_score, all_signals = calculate_pre_assessment_scores(self.session)
        scores = domain_score.as_dict()
        self.assertTrue(all(v == 0 for v in scores.values()))
        self.assertEqual(len(all_signals), 0)

    def test_single_activity_scores_correctly(self):
        """A single activity produces only its own signals."""
        self._create_activity(3, {
            'pin_order': [{'panel': 'frontend_render'}],
        })
        domain_score, all_signals = calculate_pre_assessment_scores(self.session)
        scores = domain_score.as_dict()
        self.assertEqual(scores['frontend'], 4)
        self.assertEqual(scores['backend'], 0)
        self.assertIn(3, all_signals)
        self.assertIn('frontend_render_first', all_signals[3])


class ContextModifierTests(TestCase):
    """Test context intake modifiers."""

    def test_built_something_reduces_scores(self):
        """Experienced users get 15% score reduction."""
        user = User.objects.create_user(username='exp_user', password='testpass')
        session = AssessmentSession.objects.create(
            user=user,
            prior_experience='built_something',
        )
        scores = {'backend': 10, 'frontend': 8, 'devops': 6,
                  'data_eng': 4, 'ai_ml': 3, 'cybersecurity': 2, 'product_eng': 1}
        _apply_context_modifiers(session, scores)
        self.assertAlmostEqual(scores['backend'], 10 * 0.85, places=2)

    def test_dabbled_reduces_less(self):
        """Dabbled users get 5% reduction."""
        user = User.objects.create_user(username='dab_user', password='testpass')
        session = AssessmentSession.objects.create(
            user=user,
            prior_experience='dabbled',
        )
        scores = {'backend': 10, 'frontend': 8, 'devops': 6,
                  'data_eng': 4, 'ai_ml': 3, 'cybersecurity': 2, 'product_eng': 1}
        _apply_context_modifiers(session, scores)
        self.assertAlmostEqual(scores['backend'], 10 * 0.95, places=2)

    def test_never_no_reduction(self):
        """No experience = no reduction."""
        user = User.objects.create_user(username='new_user', password='testpass')
        session = AssessmentSession.objects.create(
            user=user,
            prior_experience='never',
        )
        scores = {'backend': 10, 'frontend': 8, 'devops': 6,
                  'data_eng': 4, 'ai_ml': 3, 'cybersecurity': 2, 'product_eng': 1}
        original = scores.copy()
        _apply_context_modifiers(session, scores)
        # No experience modifier, but goal might apply
        self.assertEqual(scores['backend'], original['backend'])

    def test_exploring_boosts_lower_scores(self):
        """Exploring goal boosts below-average scores."""
        user = User.objects.create_user(username='explore_user', password='testpass')
        session = AssessmentSession.objects.create(
            user=user,
            prior_experience='never',
            goal='exploring',
        )
        scores = {'backend': 10, 'frontend': 8, 'devops': 6,
                  'data_eng': 2, 'ai_ml': 1, 'cybersecurity': 1, 'product_eng': 1}
        _apply_context_modifiers(session, scores)
        # Low scores should be boosted
        self.assertGreater(scores['product_eng'], 1)

    def test_experienced_user_not_pushed_to_unrelated_domains(self):
        """An experienced backend user's top domain shouldn't flip to something unrelated."""
        user = User.objects.create_user(username='backend_exp', password='testpass')
        session = AssessmentSession.objects.create(
            user=user,
            prior_experience='built_something',
            goal='validating',
        )
        scores = {'backend': 20, 'frontend': 5, 'devops': 15,
                  'data_eng': 3, 'ai_ml': 2, 'cybersecurity': 8, 'product_eng': 4}
        _apply_context_modifiers(session, scores)
        # Backend should still be #1 after modifiers
        top_domain = max(scores, key=scores.get)
        self.assertEqual(top_domain, 'backend',
                         "Experienced user's top domain shouldn't flip")


class ThinkingStyleDifferentiationTests(TestCase):
    """Test that thinking styles with overlapping domains produce different scores."""

    def test_systems_thinker_differs_from_reliability_keeper(self):
        """Systems Thinker and Reliability Keeper must have different confidence
        with backend=10, devops=8 (same primary domains, different weights)."""
        from assessment.thinking_styles import calculate_style_scores

        scores = {
            'backend': 10, 'frontend': 2, 'devops': 8,
            'data_eng': 1, 'ai_ml': 1, 'cybersecurity': 1, 'product_eng': 1,
        }
        styles = calculate_style_scores(scores)
        style_map = {s['style_key']: s['confidence'] for s in styles}

        systems = style_map['systems_thinker']
        reliability = style_map['reliability_keeper']

        self.assertNotEqual(
            systems, reliability,
            f"Systems Thinker ({systems}) must differ from "
            f"Reliability Keeper ({reliability})",
        )
        # Systems Thinker emphasizes backend (0.65), so with backend=10 > devops=8
        # it should score higher than Reliability Keeper which emphasizes devops (0.7)
        self.assertGreater(
            systems, reliability,
            "With backend > devops, Systems Thinker should score higher",
        )

    def test_reversed_scores_flip_ranking(self):
        """When devops > backend, Reliability Keeper should score higher."""
        from assessment.thinking_styles import calculate_style_scores

        scores = {
            'backend': 6, 'frontend': 2, 'devops': 12,
            'data_eng': 1, 'ai_ml': 1, 'cybersecurity': 1, 'product_eng': 1,
        }
        styles = calculate_style_scores(scores)
        style_map = {s['style_key']: s['confidence'] for s in styles}

        self.assertGreater(
            style_map['reliability_keeper'],
            style_map['systems_thinker'],
            "With devops > backend, Reliability Keeper should score higher",
        )
