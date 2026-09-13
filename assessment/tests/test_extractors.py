"""
Unit tests for all 6 activity signal extractors.

Tests positive fixtures (known signal-triggering payloads),
negative fixtures (non-triggering), mutual exclusion, and edge cases.
"""

from django.test import TestCase
from assessment.scoring import (
    extract_signals_activity_1,
    extract_signals_activity_2,
    extract_signals_activity_3,
    extract_signals_activity_4,
    extract_signals_activity_5,
    extract_signals_activity_6,
    calculate_activity_scores,
)
from assessment.signals_config import ACTIVITY_SIGNALS


# ─── Activity 1: System Flow ────────────────────────────────────────────────

class Activity1ExtractorTests(TestCase):
    """Tests for extract_signals_activity_1."""

    def test_api_db_prioritized_early(self):
        """API Gateway + Database in first 3 placements triggers signal."""
        data = {
            'placement_order': [
                {'label': 'API Gateway'},
                {'label': 'Database'},
                {'label': 'User Request'},
            ],
            'final_positions': [],
        }
        signals = extract_signals_activity_1(data)
        self.assertIn('api_db_prioritized_early', signals)

    def test_api_db_not_early(self):
        """API Gateway + Database NOT in first 3 placements."""
        data = {
            'placement_order': [
                {'label': 'User Request'},
                {'label': 'ML Model'},
                {'label': 'UI Response'},
                {'label': 'API Gateway'},
                {'label': 'Database'},
            ],
            'final_positions': [],
        }
        signals = extract_signals_activity_1(data)
        self.assertNotIn('api_db_prioritized_early', signals)

    def test_ml_model_logically_positioned(self):
        """ML Model after App Server triggers signal."""
        data = {
            'placement_order': [],
            'final_positions': [
                {'label': 'User Request'},
                {'label': 'Application Server'},
                {'label': 'ML Model'},
                {'label': 'UI Response'},
            ],
        }
        signals = extract_signals_activity_1(data)
        self.assertIn('ml_model_included_logically', signals)

    def test_ml_model_before_app_server(self):
        """ML Model before App Server does NOT trigger."""
        data = {
            'placement_order': [],
            'final_positions': [
                {'label': 'ML Model'},
                {'label': 'Application Server'},
                {'label': 'UI Response'},
            ],
        }
        signals = extract_signals_activity_1(data)
        self.assertNotIn('ml_model_included_logically', signals)

    def test_ui_response_anchored(self):
        """UI Response as last element triggers signal."""
        data = {
            'placement_order': [],
            'final_positions': [
                {'label': 'User Request'},
                {'label': 'API Gateway'},
                {'label': 'UI Response'},
            ],
        }
        signals = extract_signals_activity_1(data)
        self.assertIn('ui_response_anchored', signals)

    def test_ui_response_not_last(self):
        """UI Response NOT last does NOT trigger."""
        data = {
            'placement_order': [],
            'final_positions': [
                {'label': 'UI Response'},
                {'label': 'User Request'},
            ],
        }
        signals = extract_signals_activity_1(data)
        self.assertNotIn('ui_response_anchored', signals)

    def test_correct_full_flow(self):
        """Perfect ordering triggers correct_full_flow."""
        data = {
            'placement_order': [],
            'final_positions': [
                {'label': 'User Request'},
                {'label': 'API Gateway'},
                {'label': 'Application Server'},
                {'label': 'Database'},
                {'label': 'ML Model'},
                {'label': 'UI Response'},
            ],
        }
        signals = extract_signals_activity_1(data)
        self.assertIn('correct_full_flow', signals)
        self.assertIn('ui_response_anchored', signals)
        self.assertIn('ml_model_included_logically', signals)

    def test_empty_data(self):
        """Empty payload returns no signals."""
        signals = extract_signals_activity_1({})
        self.assertEqual(signals, [])

    def test_empty_lists(self):
        """Empty lists return no signals."""
        data = {'placement_order': [], 'final_positions': []}
        signals = extract_signals_activity_1(data)
        self.assertEqual(signals, [])


# ─── Activity 2: Messy UI Fix ───────────────────────────────────────────────

class Activity2ExtractorTests(TestCase):
    """Tests for extract_signals_activity_2."""

    def test_error_message_paired(self):
        """Error message adjacent to Email triggers signal."""
        data = {
            'final_positions': [
                {'label': 'Page Title'},
                {'label': 'Email'},
                {'label': 'Error Message'},
                {'label': 'Password'},
                {'label': 'Submit Button'},
            ],
            'timing': {},
        }
        signals = extract_signals_activity_2(data)
        self.assertIn('error_message_paired_to_field', signals)

    def test_error_message_far_from_email(self):
        """Error message far from Email does NOT trigger."""
        data = {
            'final_positions': [
                {'label': 'Error Message'},
                {'label': 'Page Title'},
                {'label': 'Password'},
                {'label': 'Email'},
                {'label': 'Submit Button'},
            ],
            'timing': {},
        }
        signals = extract_signals_activity_2(data)
        self.assertNotIn('error_message_paired_to_field', signals)

    def test_hierarchy_correct(self):
        """Title at top, Submit at bottom triggers signal."""
        data = {
            'final_positions': [
                {'label': 'Page Title'},
                {'label': 'Email'},
                {'label': 'Password'},
                {'label': 'Submit Button'},
            ],
            'timing': {},
        }
        signals = extract_signals_activity_2(data)
        self.assertIn('hierarchy_title_top_button_bottom', signals)

    def test_grouped_inputs(self):
        """Email + Password adjacent triggers signal."""
        data = {
            'final_positions': [
                {'label': 'Page Title'},
                {'label': 'Email'},
                {'label': 'Password'},
                {'label': 'Submit Button'},
            ],
            'timing': {},
        }
        signals = extract_signals_activity_2(data)
        self.assertIn('grouped_related_inputs', signals)

    def test_time_spent_on_error_message(self):
        """More than 5 seconds on error message triggers signal."""
        data = {
            'final_positions': [{'label': 'Page Title'}],
            'timing': {'error_message_ms': 6000},
        }
        signals = extract_signals_activity_2(data)
        self.assertIn('time_spent_on_error_message', signals)

    def test_time_not_enough(self):
        """Less than 5 seconds does NOT trigger."""
        data = {
            'final_positions': [{'label': 'Page Title'}],
            'timing': {'error_message_ms': 3000},
        }
        signals = extract_signals_activity_2(data)
        self.assertNotIn('time_spent_on_error_message', signals)

    def test_empty_data(self):
        signals = extract_signals_activity_2({})
        self.assertEqual(signals, [])


# ─── Activity 3: Debug Dashboard ────────────────────────────────────────────

class Activity3ExtractorTests(TestCase):
    """Tests for extract_signals_activity_3."""

    def test_db_log_first(self):
        data = {'pin_order': [{'panel': 'db_log'}, {'panel': 'network_tab'}]}
        signals = extract_signals_activity_3(data)
        self.assertIn('db_log_first', signals)
        self.assertEqual(len(signals), 1, "Only one first-panel signal should trigger")

    def test_deployment_history_first(self):
        data = {'pin_order': [{'panel': 'deployment_history'}, {'panel': 'db_log'}]}
        signals = extract_signals_activity_3(data)
        self.assertIn('deployment_history_first', signals)
        self.assertNotIn('db_log_first', signals)

    def test_frontend_render_first(self):
        data = {'pin_order': [{'panel': 'frontend_render'}]}
        signals = extract_signals_activity_3(data)
        self.assertIn('frontend_render_first', signals)

    def test_mutual_exclusion(self):
        """Only one first-panel signal fires, even with multiple pins."""
        data = {
            'pin_order': [
                {'panel': 'server_cpu'},
                {'panel': 'db_log'},
                {'panel': 'frontend_render'},
            ]
        }
        signals = extract_signals_activity_3(data)
        self.assertEqual(signals, ['server_cpu_first'])

    def test_empty_pin_order(self):
        signals = extract_signals_activity_3({'pin_order': []})
        self.assertEqual(signals, [])

    def test_unknown_panel(self):
        data = {'pin_order': [{'panel': 'unknown_panel'}]}
        signals = extract_signals_activity_3(data)
        self.assertEqual(signals, [])


# ─── Activity 4: Architecture Builder ───────────────────────────────────────

class Activity4ExtractorTests(TestCase):
    """Tests for extract_signals_activity_4."""

    def test_load_balancer_monitoring_early(self):
        data = {
            'selection_order': [
                {'tile': 'Load Balancer'},
                {'tile': 'Monitoring'},
                {'tile': 'Database'},
            ]
        }
        signals = extract_signals_activity_4(data)
        self.assertIn('load_balancer_monitoring_early', signals)

    def test_redis_db_prioritized(self):
        data = {
            'selection_order': [
                {'tile': 'Redis'},
                {'tile': 'Database'},
                {'tile': 'Docker'},
            ]
        }
        signals = extract_signals_activity_4(data)
        self.assertIn('redis_db_prioritized', signals)

    def test_firewall_early(self):
        data = {
            'selection_order': [
                {'tile': 'Firewall'},
                {'tile': 'Database'},
            ]
        }
        signals = extract_signals_activity_4(data)
        self.assertIn('firewall_added_early', signals)

    def test_cdn_included(self):
        data = {'selection_order': [{'tile': 'CDN'}, {'tile': 'Database'}]}
        signals = extract_signals_activity_4(data)
        self.assertIn('cdn_included', signals)

    def test_docker_selected(self):
        data = {'selection_order': [{'tile': 'Docker'}]}
        signals = extract_signals_activity_4(data)
        self.assertIn('docker_selected', signals)

    def test_ml_model_included(self):
        data = {'selection_order': [{'tile': 'ML Model'}]}
        signals = extract_signals_activity_4(data)
        self.assertIn('ml_model_included', signals)

    def test_empty_selections(self):
        signals = extract_signals_activity_4({'selection_order': []})
        self.assertEqual(signals, [])


# ─── Activity 5: Threat Spotter ─────────────────────────────────────────────

class Activity5ExtractorTests(TestCase):
    """Tests for extract_signals_activity_5."""

    def test_url_token_flagged_first(self):
        data = {
            'flag_order': [
                {'vulnerability': 'session_token_url'},
                {'vulnerability': 'plain_text_password'},
            ],
            'time_to_first_flag_ms': 5000,
        }
        signals = extract_signals_activity_5(data)
        self.assertIn('url_token_flagged_first', signals)
        self.assertIn('speed_under_8s', signals)

    def test_url_token_not_first(self):
        """URL token flagged AFTER password does NOT trigger order signal."""
        data = {
            'flag_order': [
                {'vulnerability': 'plain_text_password'},
                {'vulnerability': 'session_token_url'},
            ],
            'time_to_first_flag_ms': 3000,
        }
        signals = extract_signals_activity_5(data)
        self.assertNotIn('url_token_flagged_first', signals)
        self.assertIn('plain_text_password_flagged', signals)

    def test_all_vulnerabilities_flagged(self):
        data = {
            'flag_order': [
                {'vulnerability': 'session_token_url'},
                {'vulnerability': 'plain_text_password'},
                {'vulnerability': 'no_rate_limit'},
                {'vulnerability': 'missing_captcha'},
            ],
            'time_to_first_flag_ms': 4000,
        }
        signals = extract_signals_activity_5(data)
        self.assertIn('url_token_flagged_first', signals)
        self.assertIn('plain_text_password_flagged', signals)
        self.assertIn('no_rate_limit_flagged', signals)
        self.assertIn('missing_captcha_flagged', signals)
        self.assertIn('speed_under_8s', signals)

    def test_speed_over_8s(self):
        data = {
            'flag_order': [{'vulnerability': 'no_rate_limit'}],
            'time_to_first_flag_ms': 10000,
        }
        signals = extract_signals_activity_5(data)
        self.assertNotIn('speed_under_8s', signals)

    def test_empty_flags(self):
        signals = extract_signals_activity_5({'flag_order': []})
        self.assertEqual(signals, [])


# ─── Activity 6: Feature Triage ─────────────────────────────────────────────

class Activity6ExtractorTests(TestCase):
    """Tests for extract_signals_activity_6."""

    def test_2fa_shipped(self):
        data = {'categories': {'ship': ['2FA'], 'reconsider': [], 'cut': []}}
        signals = extract_signals_activity_6(data)
        self.assertIn('2fa_shipped', signals)

    def test_in_app_notifs_reconsidered(self):
        data = {
            'categories': {
                'ship': [],
                'reconsider': ['In-App Notifications'],
                'cut': [],
            }
        }
        signals = extract_signals_activity_6(data)
        self.assertIn('in_app_notifs_reconsidered', signals)

    def test_ai_onboarding_shipped(self):
        data = {'categories': {'ship': ['AI Onboarding'], 'reconsider': [], 'cut': []}}
        signals = extract_signals_activity_6(data)
        self.assertIn('ai_onboarding_shipped', signals)

    def test_profile_badges_cut(self):
        data = {'categories': {'ship': [], 'reconsider': [], 'cut': ['Profile Badges']}}
        signals = extract_signals_activity_6(data)
        self.assertIn('profile_badges_cut', signals)

    def test_dark_mode_shipped(self):
        data = {'categories': {'ship': ['Dark Mode'], 'reconsider': [], 'cut': []}}
        signals = extract_signals_activity_6(data)
        self.assertIn('dark_mode_shipped', signals)

    def test_no_matching_categories(self):
        """Features in wrong categories don't trigger signals."""
        data = {
            'categories': {
                'ship': ['Profile Badges'],
                'reconsider': ['Dark Mode'],
                'cut': ['2FA'],
            }
        }
        signals = extract_signals_activity_6(data)
        self.assertEqual(signals, [])

    def test_empty_categories(self):
        signals = extract_signals_activity_6({'categories': {}})
        self.assertEqual(signals, [])

    def test_missing_categories_key(self):
        signals = extract_signals_activity_6({})
        self.assertEqual(signals, [])


# ─── Score Mapping Tests ────────────────────────────────────────────────────

class ScoreMappingTests(TestCase):
    """Test that signal keys produce expected domain deltas via calculate_activity_scores."""

    def test_activity_1_correct_flow_scores(self):
        """Correct full flow should give backend:2, frontend:1, devops:1."""
        data = {
            'placement_order': [],
            'final_positions': [
                {'label': 'User Request'},
                {'label': 'API Gateway'},
                {'label': 'Application Server'},
                {'label': 'Database'},
                {'label': 'ML Model'},
                {'label': 'UI Response'},
            ],
        }
        deltas, signals = calculate_activity_scores(1, data)
        self.assertIn('correct_full_flow', signals)
        self.assertGreaterEqual(deltas['backend'], 2)
        self.assertGreaterEqual(deltas['frontend'], 1)

    def test_activity_3_db_log_first_scores(self):
        """db_log_first should give backend:4."""
        data = {'pin_order': [{'panel': 'db_log'}]}
        deltas, signals = calculate_activity_scores(3, data)
        self.assertEqual(deltas['backend'], 4)

    def test_activity_5_all_security_scores(self):
        """All security flags should accumulate cybersecurity points."""
        data = {
            'flag_order': [
                {'vulnerability': 'session_token_url'},
                {'vulnerability': 'plain_text_password'},
                {'vulnerability': 'no_rate_limit'},
                {'vulnerability': 'missing_captcha'},
            ],
            'time_to_first_flag_ms': 3000,
        }
        deltas, signals = calculate_activity_scores(5, data)
        self.assertGreaterEqual(deltas['cybersecurity'], 12)

    def test_invalid_activity_number(self):
        """Invalid activity number returns zero deltas."""
        deltas, signals = calculate_activity_scores(99, {})
        self.assertEqual(signals, [])
        self.assertTrue(all(v == 0 for v in deltas.values()))
