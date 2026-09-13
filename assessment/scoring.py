"""
Deterministic scoring engine for Make Your Move.

Processes behavioral signals from the 6 pre-assessment activities
and maps them to domain scores. No AI involved — pure rule-based logic.
"""

from .signals_config import ACTIVITY_SIGNALS, VALIDATION_MULTIPLIERS, DOMAINS


def extract_signals_activity_1(response_data):
    """
    Activity 1: System Flow Arrangement
    Analyze how user ordered: User Request, API Gateway, App Server, DB, ML Model, UI Response.
    """
    triggered = []
    order = response_data.get('placement_order', [])
    final_positions = response_data.get('final_positions', [])

    # Check if API Gateway + Database were placed in first 3
    early_placements = order[:3] if len(order) >= 3 else order
    early_labels = [item.get('label', '') for item in early_placements]

    if 'API Gateway' in early_labels and 'Database' in early_labels:
        triggered.append('api_db_prioritized_early')

    # Check if ML Model is in a logical position (after App Server, before UI Response)
    if final_positions:
        labels = [item.get('label', '') for item in final_positions]
        if 'ML Model' in labels:
            ml_idx = labels.index('ML Model')
            app_idx = labels.index('Application Server') if 'Application Server' in labels else -1
            if app_idx >= 0 and ml_idx > app_idx:
                triggered.append('ml_model_included_logically')

    # Check if UI Response is last
    if final_positions and final_positions[-1].get('label') == 'UI Response':
        triggered.append('ui_response_anchored')

    # Check for correct full flow
    expected = ['User Request', 'API Gateway', 'Application Server', 'Database', 'ML Model', 'UI Response']
    actual_labels = [item.get('label', '') for item in final_positions] if final_positions else []
    if actual_labels == expected:
        triggered.append('correct_full_flow')

    # Check for data pipeline awareness: Database before ML Model
    if final_positions:
        labels = [item.get('label', '') for item in final_positions]
        if 'Database' in labels and 'ML Model' in labels:
            db_idx = labels.index('Database')
            ml_idx = labels.index('ML Model')
            if db_idx < ml_idx:
                triggered.append('data_flow_awareness')

    return triggered


def extract_signals_activity_2(response_data):
    """
    Activity 2: Messy UI Fix
    Analyze how user fixed a scrambled registration form.
    """
    triggered = []
    final_positions = response_data.get('final_positions', [])
    timing = response_data.get('timing', {})

    if final_positions:
        labels = [item.get('label', '') for item in final_positions]

        # Check if error message is placed near its related field
        if 'Error Message' in labels and 'Email' in labels:
            err_idx = labels.index('Error Message')
            email_idx = labels.index('Email')
            if abs(err_idx - email_idx) <= 1:
                triggered.append('error_message_paired_to_field')

        # Check hierarchy: Title at top, Submit at bottom
        if labels and labels[0] == 'Page Title' and labels[-1] == 'Submit Button':
            triggered.append('hierarchy_title_top_button_bottom')

        # Check if email + password are grouped
        if 'Email' in labels and 'Password' in labels:
            email_idx = labels.index('Email')
            pw_idx = labels.index('Password')
            if abs(email_idx - pw_idx) == 1:
                triggered.append('grouped_related_inputs')

    # Time spent on error message placement (> 5 seconds = significant)
    error_time = timing.get('error_message_ms', 0)
    if error_time > 5000:
        triggered.append('time_spent_on_error_message')

    return triggered


def extract_signals_activity_3(response_data):
    """
    Activity 3: Live Debug Dashboard
    Analyze which panel user investigated first with pins.
    """
    triggered = []
    pin_order = response_data.get('pin_order', [])

    if pin_order:
        first_panel = pin_order[0].get('panel', '')

        panel_signal_map = {
            'db_log': 'db_log_first',
            'deployment_history': 'deployment_history_first',
            'server_cpu': 'server_cpu_first',
            'network_tab': 'network_tab_first',
            'frontend_render': 'frontend_render_first',
        }

        signal = panel_signal_map.get(first_panel)
        if signal:
            triggered.append(signal)

    return triggered


def extract_signals_activity_4(response_data):
    """
    Activity 4: Architecture Builder
    Analyze which tiles were selected and in what order for 1M users scenario.
    """
    triggered = []
    selection_order = response_data.get('selection_order', [])
    selected_tiles = [item.get('tile', '') for item in selection_order]

    # Early = in first 3 selections
    early_selections = selected_tiles[:3] if len(selected_tiles) >= 3 else selected_tiles

    if 'Load Balancer' in early_selections and 'Monitoring' in early_selections:
        triggered.append('load_balancer_monitoring_early')

    if 'Redis' in selected_tiles and 'Database' in selected_tiles:
        redis_idx = selected_tiles.index('Redis')
        db_idx = selected_tiles.index('Database')
        if redis_idx < 4 and db_idx < 4:
            triggered.append('redis_db_prioritized')

    if 'Firewall' in early_selections:
        triggered.append('firewall_added_early')

    if 'CDN' in selected_tiles:
        triggered.append('cdn_included')

    if 'Docker' in selected_tiles:
        triggered.append('docker_selected')

    if 'ML Model' in selected_tiles:
        triggered.append('ml_model_included')

    if 'Message Queue' in selected_tiles:
        triggered.append('message_queue_selected')

    return triggered


def extract_signals_activity_5(response_data):
    """
    Activity 5: Threat Spotter
    Analyze which vulnerabilities were flagged and in what order.
    """
    triggered = []
    flag_order = response_data.get('flag_order', [])
    time_to_first_flag = response_data.get('time_to_first_flag_ms', None)

    if flag_order:
        flag_labels = [item.get('vulnerability', '') for item in flag_order]

        # Check if URL token flagged before DOM password
        if 'session_token_url' in flag_labels and 'plain_text_password' in flag_labels:
            url_idx = flag_labels.index('session_token_url')
            pwd_idx = flag_labels.index('plain_text_password')
            if url_idx < pwd_idx:
                triggered.append('url_token_flagged_first')

        if 'plain_text_password' in flag_labels:
            triggered.append('plain_text_password_flagged')

        if 'no_rate_limit' in flag_labels:
            triggered.append('no_rate_limit_flagged')

        if 'missing_captcha' in flag_labels:
            triggered.append('missing_captcha_flagged')

    # Speed check: first flag under 8 seconds
    if time_to_first_flag is not None and time_to_first_flag < 8000:
        triggered.append('speed_under_8s')

    return triggered


def extract_signals_activity_6(response_data):
    """
    Activity 6: Feature Triage
    Analyze which features were placed in Ship/Reconsider/Cut.
    """
    triggered = []
    categories = response_data.get('categories', {})
    ship = categories.get('ship', [])
    reconsider = categories.get('reconsider', [])
    cut = categories.get('cut', [])

    if '2FA' in ship:
        triggered.append('2fa_shipped')

    if 'In-App Notifications' in reconsider:
        triggered.append('in_app_notifs_reconsidered')

    if 'AI Onboarding' in ship:
        triggered.append('ai_onboarding_shipped')

    if 'Profile Badges' in cut:
        triggered.append('profile_badges_cut')

    if 'Dark Mode' in ship:
        triggered.append('dark_mode_shipped')

    return triggered


# Map activity numbers to their signal extractor functions
SIGNAL_EXTRACTORS = {
    1: extract_signals_activity_1,
    2: extract_signals_activity_2,
    3: extract_signals_activity_3,
    4: extract_signals_activity_4,
    5: extract_signals_activity_5,
    6: extract_signals_activity_6,
}


def calculate_activity_scores(activity_number, response_data):
    """
    Calculate domain score deltas for a single activity.

    Returns:
        dict: {domain: score_delta} for triggered signals
        list: list of triggered signal keys
    """
    extractor = SIGNAL_EXTRACTORS.get(activity_number)
    if not extractor:
        return {d: 0 for d in DOMAINS}, []

    triggered_signals = extractor(response_data)
    activity_signals = ACTIVITY_SIGNALS.get(activity_number, {})

    score_deltas = {d: 0 for d in DOMAINS}
    for signal_key in triggered_signals:
        signal_config = activity_signals.get(signal_key, {})
        for domain, points in signal_config.get('scores', {}).items():
            score_deltas[domain] += points

    return score_deltas, triggered_signals


def calculate_pre_assessment_scores(session):
    """
    Calculate aggregate domain scores across all 6 activities.
    Updates the DomainScore model for the session.
    """
    from .models import DomainScore, ActivityResponse

    total_scores = {d: 0 for d in DOMAINS}
    all_signals = {}

    responses = ActivityResponse.objects.filter(session=session)
    for response in responses:
        deltas, triggered = calculate_activity_scores(
            response.activity_number,
            response.response_data
        )
        for domain in DOMAINS:
            total_scores[domain] += deltas[domain]
        all_signals[response.activity_number] = triggered

    # Apply context intake modifiers
    _apply_context_modifiers(session, total_scores)

    # Save to DomainScore
    domain_score, _ = DomainScore.objects.update_or_create(
        session=session,
        defaults=total_scores,
    )

    return domain_score, all_signals


def _apply_context_modifiers(session, scores):
    """
    Apply context intake modifiers to scores.
    Prior experience raises thresholds to prevent confirmation bias.

    Design note (§6.5): The 'built_something' penalty applies a uniform
    0.85× multiplier across ALL domains. This is an accepted limitation
    because the context intake does not collect domain-specific experience.
    A uniform reduction preserves relative ranking while tempering absolute
    scores for experienced users — it cannot push an experienced user toward
    an unrelated domain. The 'validating' goal modifier further amplifies
    the user's existing top scores, reinforcing the correct rank order.
    """
    if session.prior_experience == 'built_something':
        # Raise threshold: reduce all scores slightly to prevent early confirmation
        for domain in DOMAINS:
            scores[domain] = max(0, scores[domain] * 0.85)
    elif session.prior_experience == 'dabbled':
        for domain in DOMAINS:
            scores[domain] = max(0, scores[domain] * 0.95)

    # Goal affects distribution
    if session.goal == 'exploring':
        # Wider spread: boost lower scores slightly
        avg = sum(scores.values()) / len(scores) if scores else 0
        for domain in DOMAINS:
            if scores[domain] < avg:
                scores[domain] += avg * 0.1
    elif session.goal == 'validating':
        # Tighter depth: boost top scores
        max_score = max(scores.values()) if scores else 0
        for domain in DOMAINS:
            if scores[domain] >= max_score * 0.8:
                scores[domain] *= 1.1


def apply_validation_multipliers(session):
    """
    Apply validation stage multipliers to existing domain scores.

    Records pre-validation and post-validation snapshots for auditability.
    Returns the updated DomainScore with a `validation_audit` attribute
    containing the before/after data.
    """
    import logging
    from .models import DomainScore, ValidationResponse

    logger = logging.getLogger(__name__)

    try:
        domain_score = DomainScore.objects.get(session=session)
    except DomainScore.DoesNotExist:
        return None

    if domain_score.validation_applied:
        return domain_score

    # Snapshot pre-validation scores and ranking
    pre_validation = domain_score.as_dict()
    pre_ranked = sorted(pre_validation, key=pre_validation.get, reverse=True)

    validations = ValidationResponse.objects.filter(session=session)

    # Map validation domains to score fields
    domain_field_map = {
        'frontend_product': ['frontend', 'product_eng'],
        'backend_devops': ['backend', 'devops'],
        'data_ai': ['data_eng', 'ai_ml'],
        'cybersecurity': ['cybersecurity'],
    }

    for validation in validations:
        multiplier = VALIDATION_MULTIPLIERS.get(validation.engagement_level, 1.0)
        fields = domain_field_map.get(validation.domain, [])
        for field in fields:
            current = getattr(domain_score, field, 0)
            setattr(domain_score, field, current * multiplier)

    # Snapshot post-validation scores and ranking
    post_validation = domain_score.as_dict()
    post_ranked = sorted(post_validation, key=post_validation.get, reverse=True)

    # Log rank changes for auditability
    rank_changes = []
    for domain in DOMAINS:
        pre_rank = pre_ranked.index(domain) + 1
        post_rank = post_ranked.index(domain) + 1
        if pre_rank != post_rank:
            rank_changes.append(
                f"{domain}: rank {pre_rank} → {post_rank}"
            )

    if rank_changes:
        logger.info(
            "Validation rank changes for session %s: %s",
            session.id, "; ".join(rank_changes),
        )

    # Attach audit data as a transient attribute (not persisted)
    domain_score._validation_audit = {
        'pre_validation': pre_validation,
        'post_validation': post_validation,
        'rank_changes': rank_changes,
    }

    domain_score.validation_applied = True
    domain_score.save()
    return domain_score


def get_final_results(session):
    """
    Get the final ranked domain results for a session.
    """
    from .models import DomainScore

    try:
        domain_score = DomainScore.objects.get(session=session)
    except DomainScore.DoesNotExist:
        return []

    return domain_score.get_ranked_domains()
