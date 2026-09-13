"""
Scoring signal configuration for all 6 pre-assessment activities.

Maps behavioral signals observed during activities to domain score deltas.
This is the single source of truth for all scoring rules from the spec.
"""

# Domain keys used throughout the scoring engine
DOMAINS = [
    'backend', 'frontend', 'devops', 'data_eng',
    'ai_ml', 'cybersecurity', 'product_eng',
]


# ─── Activity 1: System Flow Arrangement ───────────────────────────────────────
# Drag 6 unlabelled blocks: User Request, API Gateway, Application Server,
# Database, ML Model, UI Response
ACTIVITY_1_SIGNALS = {
    'api_db_prioritized_early': {
        'description': 'API + DB prioritized early in the flow',
        'scores': {'backend': 3, 'devops': 1},
    },
    'ml_model_included_logically': {
        'description': 'ML Model included in a logical position',
        'scores': {'ai_ml': 3, 'data_eng': 2},
    },
    'ui_response_anchored': {
        'description': 'UI Response anchored at the end',
        'scores': {'frontend': 3},
    },
    'load_balancer_mentioned_retry': {
        'description': 'Load balancer/monitoring mentioned in retry',
        'scores': {'devops': 3, 'backend': 1},
    },
    'correct_full_flow': {
        'description': 'Correct end-to-end flow order',
        'scores': {'backend': 2, 'frontend': 1, 'devops': 1},
    },
    'data_flow_awareness': {
        'description': 'Database positioned before ML Model, showing data pipeline thinking',
        'scores': {'data_eng': 3, 'backend': 1},
    },
}


# ─── Activity 2: Messy UI Fix ──────────────────────────────────────────────────
# Fix a registration form with scrambled elements
ACTIVITY_2_SIGNALS = {
    'error_message_paired_to_field': {
        'description': 'Error message paired to its field',
        'scores': {'frontend': 3, 'product_eng': 2},
    },
    'hierarchy_title_top_button_bottom': {
        'description': 'Title at top, Submit button at bottom',
        'scores': {'frontend': 3},
    },
    'grouped_related_inputs': {
        'description': 'Grouped related inputs (email + password)',
        'scores': {'product_eng': 3, 'frontend': 1},
    },
    'time_spent_on_error_message': {
        'description': 'Significant time spent on error message placement',
        'scores': {'backend': 2, 'devops': 1},
    },
}


# ─── Activity 3: Live Debug Dashboard ──────────────────────────────────────────
# Drag pins to panels: DB log, Network tab, Server CPU, Frontend render, Deploy history
ACTIVITY_3_SIGNALS = {
    'db_log_first': {
        'description': 'DB query log investigated first',
        'scores': {'backend': 4},
    },
    'deployment_history_first': {
        'description': 'Deployment history investigated first',
        'scores': {'devops': 4, 'backend': 1},
    },
    'server_cpu_first': {
        'description': 'Server CPU investigated first',
        'scores': {'devops': 3, 'backend': 2},
    },
    'network_tab_first': {
        'description': 'Network tab investigated first',
        'scores': {'backend': 3, 'frontend': 1},
    },
    'frontend_render_first': {
        'description': 'Frontend render investigated first',
        'scores': {'frontend': 4},
    },
}


# ─── Activity 4: Architecture Builder ──────────────────────────────────────────
# Select from 9 tiles for "1 million users" scenario
ACTIVITY_4_SIGNALS = {
    'load_balancer_monitoring_early': {
        'description': 'Load balancer + monitoring selected early',
        'scores': {'devops': 4, 'backend': 1},
    },
    'redis_db_prioritized': {
        'description': 'Redis + DB prioritized',
        'scores': {'backend': 4, 'data_eng': 3},
    },
    'firewall_added_early': {
        'description': 'Firewall added early (strong security signal)',
        'scores': {'cybersecurity': 4, 'backend': 1},
    },
    'cdn_included': {
        'description': 'CDN included in architecture',
        'scores': {'frontend': 2, 'devops': 2},
    },
    'docker_selected': {
        'description': 'Docker selected for containerization',
        'scores': {'devops': 3},
    },
    'ml_model_included': {
        'description': 'ML Model included in architecture',
        'scores': {'ai_ml': 3, 'data_eng': 2},
    },
    'message_queue_selected': {
        'description': 'Message Queue selected for async processing',
        'scores': {'data_eng': 4, 'backend': 1, 'devops': 1},
    },
}


# ─── Activity 5: Threat Spotter ────────────────────────────────────────────────
# Drag flags to login page vulnerabilities
ACTIVITY_5_SIGNALS = {
    'url_token_flagged_first': {
        'description': 'Session token in URL flagged before DOM password',
        'scores': {'cybersecurity': 4},
    },
    'plain_text_password_flagged': {
        'description': 'Plain text password in DOM flagged',
        'scores': {'cybersecurity': 3, 'frontend': 1},
    },
    'no_rate_limit_flagged': {
        'description': 'No rate-limit flagged',
        'scores': {'cybersecurity': 3, 'backend': 1},
    },
    'missing_captcha_flagged': {
        'description': 'Missing CAPTCHA flagged',
        'scores': {'backend': 2, 'cybersecurity': 2},
    },
    'speed_under_8s': {
        'description': 'First flag placed in under 8 seconds',
        'scores': {'cybersecurity': 3},
    },
}


# ─── Activity 6: Feature Triage ────────────────────────────────────────────────
# Drag feature cards to Ship / Reconsider / Cut
ACTIVITY_6_SIGNALS = {
    '2fa_shipped': {
        'description': '2FA shipped unprompted',
        'scores': {'cybersecurity': 3, 'product_eng': 2},
    },
    'in_app_notifs_reconsidered': {
        'description': 'In-app notifications to Reconsider (strong product signal)',
        'scores': {'product_eng': 4},
    },
    'ai_onboarding_shipped': {
        'description': 'AI onboarding shipped',
        'scores': {'ai_ml': 3, 'product_eng': 1},
    },
    'profile_badges_cut': {
        'description': 'Profile badges cut',
        'scores': {'product_eng': 3},
    },
    'dark_mode_shipped': {
        'description': 'Dark mode shipped',
        'scores': {'frontend': 2, 'product_eng': 1},
    },
}


# Master lookup: activity_number → signals dict
ACTIVITY_SIGNALS = {
    1: ACTIVITY_1_SIGNALS,
    2: ACTIVITY_2_SIGNALS,
    3: ACTIVITY_3_SIGNALS,
    4: ACTIVITY_4_SIGNALS,
    5: ACTIVITY_5_SIGNALS,
    6: ACTIVITY_6_SIGNALS,
}


# ─── Validation Multipliers ────────────────────────────────────────────────────
# Capped to prevent a single validation from overwhelming pre-assessment evidence.
# Previously: strong was 1.8, which allowed rank reversals.
VALIDATION_MULTIPLIERS = {
    'strong': 1.4,
    'good': 1.25,
    'partial': 1.1,
    'low': 0.9,
    'skipped': 0.8,
}


# ─── Thinking Style → Domain Mapping ──────────────────────────────────────────
# Each style has weighted primary domains to prevent identical confidence scores.
# Weights represent how strongly each primary domain contributes to the style.
THINKING_STYLE_DOMAINS = {
    'experience_shaper': {
        'name': 'The Experience Shaper',
        'primary_domains': ['frontend', 'product_eng'],
        'weights': [0.6, 0.4],
        'description': 'You instinctively design for users. You think about hierarchy, flow, and how people feel when they interact with software.',
        'icon': '🎨',
    },
    'problem_definer': {
        'name': 'The Problem Definer',
        'primary_domains': ['product_eng', 'ai_ml'],
        'weights': [0.6, 0.4],
        'description': 'You cut through noise to find the real problem. You prioritize what matters and question assumptions before building.',
        'icon': '🎯',
    },
    'systems_thinker': {
        'name': 'The Systems Thinker',
        'primary_domains': ['backend', 'devops'],
        'weights': [0.65, 0.35],
        'description': 'You see the whole machine. You think about how data flows, what breaks under load, and how components connect.',
        'icon': '⚙️',
    },
    'reliability_keeper': {
        'name': 'The Reliability Keeper',
        'primary_domains': ['devops', 'backend'],
        'weights': [0.7, 0.3],
        'description': 'You care about uptime and resilience. You instinctively think about failure modes, monitoring, and deployment safety.',
        'icon': '🛡️',
    },
    'signal_seeker': {
        'name': 'The Signal Seeker',
        'primary_domains': ['data_eng', 'ai_ml'],
        'weights': [0.6, 0.4],
        'description': 'You find patterns in noise. You gravitate toward data, look for anomalies, and think about what the numbers are telling you.',
        'icon': '📊',
    },
    'hypothesis_tester': {
        'name': 'The Hypothesis Tester',
        'primary_domains': ['ai_ml', 'data_eng'],
        'weights': [0.6, 0.4],
        'description': 'You test before you trust. You think in experiments, question model outputs, and care about validation over assumptions.',
        'icon': '🔬',
    },
    'threat_anticipator': {
        'name': 'The Threat Anticipator',
        'primary_domains': ['cybersecurity', 'backend'],
        'weights': [0.7, 0.3],
        'description': 'You see what could go wrong. You instinctively spot vulnerabilities, think adversarially, and protect before it breaks.',
        'icon': '🔒',
    },
    'trust_architect': {
        'name': 'The Trust Architect',
        'primary_domains': ['cybersecurity', 'devops'],
        'weights': [0.6, 0.4],
        'description': 'You build systems people can rely on. You think about access control, secure defaults, and infrastructure that earns trust.',
        'icon': '🏗️',
    },
}


# ─── Domain Theoretical Maxima ─────────────────────────────────────────────────
# Used for normalized ranking so domains with different scoring ranges
# compete fairly. Updated whenever signal mappings change.
DOMAIN_THEORETICAL_MAX = {
    'backend': 27,
    'frontend': 18,
    'devops': 23,
    'data_eng': 14,
    'ai_ml': 10,
    'cybersecurity': 22,
    'product_eng': 16,
}
