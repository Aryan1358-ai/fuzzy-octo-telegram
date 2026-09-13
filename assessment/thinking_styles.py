"""
Thinking Style mapping engine.

Maps domain scores to the 8 thinking style profiles.
Selects the top 3-4 styles based on domain score distribution.
"""

from .signals_config import THINKING_STYLE_DOMAINS, DOMAINS


def calculate_style_scores(domain_scores_dict):
    """
    Calculate how well a user matches each thinking style
    based on their domain scores.

    Args:
        domain_scores_dict: dict of {domain: score}

    Returns:
        list of {style_key, name, confidence, icon, description, primary_domains}
        sorted by confidence descending
    """
    total = sum(domain_scores_dict.values()) or 1

    style_scores = []

    for style_key, style_info in THINKING_STYLE_DOMAINS.items():
        primary = style_info['primary_domains']
        weights = style_info.get('weights', [0.5] * len(primary))

        # Confidence = weighted sum of primary domain scores / total
        primary_total = sum(
            domain_scores_dict.get(d, 0) * w
            for d, w in zip(primary, weights)
        )
        confidence = primary_total / total

        # Bonus for having both primary domains strong (not just one)
        if len(primary) == 2:
            d1_score = domain_scores_dict.get(primary[0], 0)
            d2_score = domain_scores_dict.get(primary[1], 0)
            if d1_score > 0 and d2_score > 0:
                balance = min(d1_score, d2_score) / max(d1_score, d2_score)
                confidence *= (1 + balance * 0.2)  # Up to 20% bonus for balance

        style_scores.append({
            'style_key': style_key,
            'name': style_info['name'],
            'confidence': round(confidence, 3),
            'icon': style_info['icon'],
            'description': style_info['description'],
            'primary_domains': primary,
        })

    # Sort by confidence descending
    style_scores.sort(key=lambda x: x['confidence'], reverse=True)
    return style_scores


def get_top_styles(domain_scores_dict, count=None):
    """
    Select the top 3-4 thinking styles for a user.

    Rules:
    - Always return at least 3 styles
    - Return 4th style if its confidence is > 60% of the 3rd style
    - Cap at 4 styles max

    Args:
        domain_scores_dict: dict of {domain: score}
        count: override count (for testing)

    Returns:
        list of top style dicts with rank added
    """
    all_styles = calculate_style_scores(domain_scores_dict)

    if count:
        top = all_styles[:count]
    else:
        # Default: top 3, plus 4th if close enough
        top = all_styles[:3]
        if len(all_styles) >= 4:
            third_conf = top[2]['confidence']
            fourth_conf = all_styles[3]['confidence']
            if third_conf > 0 and fourth_conf / third_conf > 0.6:
                top.append(all_styles[3])

    # Add rank
    for i, style in enumerate(top):
        style['rank'] = i + 1

    return top


def save_thinking_styles(session, domain_scores_dict):
    """
    Calculate and persist thinking styles for a session.
    """
    from .models import ThinkingStyle

    # Clear existing styles for this session
    ThinkingStyle.objects.filter(session=session).delete()

    top_styles = get_top_styles(domain_scores_dict)

    created = []
    for style in top_styles:
        ts = ThinkingStyle.objects.create(
            session=session,
            style_key=style['style_key'],
            confidence=style['confidence'],
            description=style['description'],
            rank=style['rank'],
        )
        created.append(ts)

    return top_styles
