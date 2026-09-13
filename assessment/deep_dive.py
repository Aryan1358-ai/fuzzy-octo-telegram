"""
Gemini-powered Conversational Deep-Dive engine.

Drives a 3–4 turn AI-led conversation grounded in the user's real behavioral
data from the assessment.  Produces personalized roadmap annotations on
completion.

Data isolation: this module NEVER touches the Stage 2/4/5 scoring pipeline.
"""

import json
import re
import logging

from django.conf import settings

from google import genai
from google.genai import types

from .signals_config import THINKING_STYLE_DOMAINS, ACTIVITY_SIGNALS

logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────────────────────
# Gemini client (lazy-initialized)
# ───────────────────────────────────────────────────────────────────────────────

_client = None


def _get_client():
    """Lazy-init the Gemini client so import-time errors don't crash Django."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


# ───────────────────────────────────────────────────────────────────────────────
# Human-readable signal descriptions (for system prompt grounding)
# ───────────────────────────────────────────────────────────────────────────────

SIGNAL_DESCRIPTIONS = {
    # Activity 1 — System Flow
    'api_db_prioritized_early': 'placed the API Gateway and Database early in a system flow',
    'ml_model_included_logically': 'included the ML Model in a logical position in the data flow',
    'ui_response_anchored': 'anchored the UI Response at the end of the pipeline',
    'correct_full_flow': 'arranged the entire system flow in the correct order',
    # Activity 2 — Messy UI Fix
    'error_message_paired_to_field': 'moved the error message right next to its related input field',
    'hierarchy_title_top_button_bottom': 'structured the form with the title at top and submit button at bottom',
    'grouped_related_inputs': 'grouped email and password inputs together',
    'time_spent_on_error_message': 'spent significant time thinking about error message placement',
    # Activity 3 — Debug Dashboard
    'db_log_first': 'investigated the database query log first when debugging',
    'deployment_history_first': 'checked the deployment history first when debugging',
    'server_cpu_first': 'looked at server CPU metrics first when debugging',
    'network_tab_first': 'opened the network tab first when debugging',
    'frontend_render_first': 'inspected the frontend render panel first when debugging',
    # Activity 4 — Architecture Builder
    'load_balancer_monitoring_early': 'selected a load balancer and monitoring early for a 1M-user system',
    'redis_db_prioritized': 'prioritized Redis and the database in the architecture',
    'firewall_added_early': 'added a firewall early in the architecture design',
    'cdn_included': 'included a CDN in the architecture',
    'docker_selected': 'chose Docker for containerization',
    'ml_model_included': 'included an ML model in the architecture',
    # Activity 5 — Threat Spotter
    'url_token_flagged_first': 'caught the session token exposed in the URL before anything else',
    'plain_text_password_flagged': 'flagged the plain-text password in the DOM',
    'no_rate_limit_flagged': 'noticed the missing rate limit on the login form',
    'missing_captcha_flagged': 'spotted the missing CAPTCHA',
    'speed_under_8s': 'spotted the first vulnerability in under 8 seconds',
    # Activity 6 — Feature Triage
    '2fa_shipped': 'chose to ship two-factor authentication unprompted',
    'in_app_notifs_reconsidered': 'placed in-app notifications in Reconsider instead of shipping directly',
    'ai_onboarding_shipped': 'shipped the AI onboarding feature',
    'profile_badges_cut': 'cut profile badges from the product launch',
    'dark_mode_shipped': 'shipped dark mode',
}

DOMAIN_LABELS = {
    'backend': 'Backend Engineering',
    'frontend': 'Frontend Engineering',
    'devops': 'DevOps Engineering',
    'data_eng': 'Data Engineering',
    'ai_ml': 'AI/ML Engineering',
    'cybersecurity': 'Cybersecurity',
    'product_eng': 'Product Engineering',
}

# ───────────────────────────────────────────────────────────────────────────────
# Behavioral context builder
# ───────────────────────────────────────────────────────────────────────────────


def _gather_behavioral_context(session):
    """
    Pull triggered signals + thinking style from the session and return a
    human-readable description for the Gemini system prompt.
    """
    from .models import ActivityResponse, ThinkingStyle
    from .scoring import SIGNAL_EXTRACTORS

    # 1. Collect triggered signals across all 6 activities
    triggered = []
    responses = ActivityResponse.objects.filter(session=session)
    for resp in responses:
        extractor = SIGNAL_EXTRACTORS.get(resp.activity_number)
        if extractor:
            signals = extractor(resp.response_data)
            for sig in signals:
                desc = SIGNAL_DESCRIPTIONS.get(sig)
                if desc:
                    triggered.append(desc)

    # 2. Get top thinking style
    top_style = ThinkingStyle.objects.filter(session=session).order_by('rank').first()
    style_name = ''
    style_desc = ''
    if top_style:
        config = THINKING_STYLE_DOMAINS.get(top_style.style_key, {})
        style_name = config.get('name', top_style.style_key)
        style_desc = config.get('description', '')

    return {
        'triggered_signals': triggered,
        'thinking_style_name': style_name,
        'thinking_style_description': style_desc,
    }


# ───────────────────────────────────────────────────────────────────────────────
# System prompt construction
# ───────────────────────────────────────────────────────────────────────────────


def _build_system_prompt(session, domain, behavioral_ctx):
    """Build the Gemini system instruction that controls the conversation."""

    domain_label = DOMAIN_LABELS.get(domain, domain)
    signals_text = '\n'.join(f'  • {s}' for s in behavioral_ctx['triggered_signals'][:6])
    style_name = behavioral_ctx['thinking_style_name'] or 'unknown'
    style_desc = behavioral_ctx['thinking_style_description'] or ''

    return f"""You are MYM, the career exploration assistant for MakeYourMove — a platform that helps students discover their ideal software engineering specialisation.

## YOUR ROLE
You are conducting a short, warm Conversational Deep-Dive with a student who just completed a behavioural assessment. The conversation is about the "{domain_label}" domain. Your goal is to **gather concrete evidence** about the student's experience, motivations, and skills so the platform can personalise their learning roadmap.

## THE STUDENT'S BEHAVIORAL PROFILE
Their top thinking style is "{style_name}" — {style_desc}

During the assessment, the student:
{signals_text if signals_text else '  • (no specific signals recorded)'}

## CONVERSATION STRUCTURE — EVIDENCE-GATHERING FUNNEL
Follow this exact structure. You output ONE message per turn.

Turn 0 (Opening): Reference a specific behavioral moment from above. Ask a broad, low-pressure question to get a personal narrative. Example pattern: "You [specific thing they did]… Have you ever done something like that for real?"

Turn 1 (Follow-up 1 — Narrowing): Pick a specific detail from the student's story. Ask about their concrete role or action. Look for: projects, technologies used, team dynamics.

Turn 2 (Follow-up 2 — Motivation): Ask about the underlying "why." What drew them to that approach? What did they enjoy or find frustrating? Look for: intrinsic motivations, strengths, gaps.

Turn 3 (Conditional — only if needed): ONLY ask this if the student's first two replies were vague (<15 words average) or you genuinely cannot distinguish passion from external motivation. Otherwise, wrap up warmly. Most conversations should END after Turn 2.

## EVIDENCE YOU ARE GATHERING
Try to naturally elicit:
- **Projects**: What the student has built or worked on
- **Technologies**: Specific tools, languages, frameworks mentioned
- **Responsibilities**: Their role in teams or projects
- **Problems solved**: Specific challenges they tackled
- **Motivations**: Why they are drawn to this area
- **Strengths**: What they're good at based on their own assessment
- **Gaps**: Areas they want to learn or feel unsure about

## RULES (CRITICAL)
1. Keep every response to ≤ 2 sentences. Be concise and conversational.
2. NEVER ask for personal identifying information (names, locations, school names, emails).
3. If the student gives a LOW-EFFORT reply (< 5 words, "idk", "ok", etc.), probe once gently ("No worries — even a small example works!"). If the next reply is also low-effort, wrap up gracefully.
4. If the student goes OFF-TOPIC, redirect once ("That's interesting — but I'm curious more about the tech side. [repeat question in different words]"). If still off-topic, wrap up gracefully.
5. If the student says something HOSTILE or INAPPROPRIATE, respond ONLY with: "Let's move on. Your roadmap is ready based on your assessment."
6. If the student mentions a PERSONAL SITUATION (health, financial, family), do NOT probe. Say something like: "I appreciate you sharing that. Let's focus on your learning path — your roadmap is ready."
7. You are NOT a therapist, mentor, or academic advisor. Stay in your lane.
8. Refer to the conversation turn number provided in the user message wrapper to know which step of the funnel you are on.
9. When wrapping up after the final turn, end with: "Thanks for sharing! I've tailored your roadmap based on what you told me. Let's check it out."
"""


# ───────────────────────────────────────────────────────────────────────────────
# Gemini generation helpers
# ───────────────────────────────────────────────────────────────────────────────


def generate_opening_line(session, domain):
    """Generate the personalized opening line using Gemini."""
    ctx = _gather_behavioral_context(session)
    system_prompt = _build_system_prompt(session, domain, ctx)

    domain_label = DOMAIN_LABELS.get(domain, domain)

    # Pick the most interesting signal to highlight
    highlight = ctx['triggered_signals'][0] if ctx['triggered_signals'] else f'explored {domain_label}'

    user_prompt = (
        f"[TURN 0 — OPENING]\n"
        f"Generate your opening message for the {domain_label} deep-dive.\n"
        f"Highlight this specific behavior: \"{highlight}\"\n"
        f"Remember: reference it naturally, then ask a broad personal question."
    )

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=150,
            ),
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini opening line failed: {e}")
        return (
            f"I noticed some interesting choices you made during the assessment — "
            f"especially around {domain_label}. "
            f"Have you ever worked on something like that outside of this exercise?"
        )


def generate_follow_up(session, domain, transcript, turn_number):
    """
    Generate a follow-up message given the conversation history.
    turn_number is the AI's current turn (1, 2, or 3).
    """
    ctx = _gather_behavioral_context(session)
    system_prompt = _build_system_prompt(session, domain, ctx)

    # Build conversation history as a single prompt with role labels
    history_lines = []
    for msg in transcript:
        role_label = "MYM" if msg['role'] == 'ai' else "Student"
        history_lines.append(f"{role_label}: {msg['content']}")

    history_text = '\n'.join(history_lines)

    turn_labels = {
        1: 'FOLLOW-UP 1 — NARROWING: Ask about a specific detail from their story.',
        2: 'FOLLOW-UP 2 — MOTIVATION: Ask about the underlying "why."',
        3: 'FOLLOW-UP 3 — DISAMBIGUATION (conditional): Only ask if intent is ambiguous. Otherwise, give a warm wrap-up.',
    }

    turn_instruction = turn_labels.get(turn_number, 'Wrap up the conversation warmly.')

    user_prompt = (
        f"[CONVERSATION SO FAR]\n{history_text}\n\n"
        f"[TURN {turn_number} — {turn_instruction}]\n"
        f"Generate your next message. Remember: ≤ 2 sentences, concise, warm."
    )

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=150,
            ),
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini follow-up failed: {e}")
        return "That's really interesting, thanks for sharing! Your roadmap has been personalised — let's check it out."


# ───────────────────────────────────────────────────────────────────────────────
# Reply classification (local — no Gemini call needed)
# ───────────────────────────────────────────────────────────────────────────────

_HOSTILE_PATTERNS = re.compile(
    r'\b(fuck|shit|damn|ass|bitch|idiot|stupid|stfu|shut\s*up|hate\s*you|kill|die)\b',
    re.IGNORECASE,
)

_PERSONAL_PATTERNS = re.compile(
    r'\b(my\s+name\s+is|i\s+live\s+in|my\s+address|my\s+phone|'
    r'i\s+have\s+depression|i\s+am\s+suicidal|mental\s+health|'
    r'family\s+problems?|financial\s+trouble|health\s+issues?)\b',
    re.IGNORECASE,
)


def classify_reply(message):
    """
    Classify a user reply for guardrail handling.

    Returns one of: 'substantive', 'low_effort', 'hostile', 'personal'.
    """
    text = message.strip()

    # Hostile check
    if _HOSTILE_PATTERNS.search(text):
        return 'hostile'

    # Personal situation check
    if _PERSONAL_PATTERNS.search(text):
        return 'personal'

    # Low-effort check (< 4 words or common non-answers)
    word_count = len(text.split())
    low_effort_phrases = {
        'ok', 'okay', 'idk', 'sure', 'yes', 'no', 'maybe', 'fine',
        'i dont know', "i don't know", 'nothing', 'nope', 'yep', 'yeah',
        'not really', 'no idea', 'dunno', 'k', 'kk', 'meh',
    }
    if word_count < 4 or text.lower().rstrip('.!?') in low_effort_phrases:
        return 'low_effort'

    return 'substantive'


# ───────────────────────────────────────────────────────────────────────────────
# Wrap-up lines (deterministic — no Gemini needed)
# ───────────────────────────────────────────────────────────────────────────────

WRAP_UP_LINES = {
    'completed': "Thanks for sharing! I've tailored your roadmap based on what you told me. Let's check it out.",
    'skipped': "No problem! Your roadmap is ready based on your assessment results.",
    'hostile': "Let's move on. Your roadmap is ready based on your assessment.",
    'personal': "I appreciate you sharing that. Let's focus on your learning path — your roadmap is ready.",
    'low_effort': "That's totally okay! Let's jump to your roadmap — it's already personalised from your assessment.",
    'error': "Something went wrong on our end. Your roadmap is ready based on your assessment results.",
}


def get_wrap_up_line(reason):
    """Return an appropriate closing line."""
    return WRAP_UP_LINES.get(reason, WRAP_UP_LINES['completed'])


# ───────────────────────────────────────────────────────────────────────────────
# Roadmap annotation generation
# ───────────────────────────────────────────────────────────────────────────────


def generate_roadmap_annotations(session, domain, transcript):
    """
    Ask Gemini to produce 2-3 brief, personalized annotations based on the
    completed chat transcript.  These annotations will be displayed alongside
    roadmap steps.
    """
    domain_label = DOMAIN_LABELS.get(domain, domain)

    # Build transcript text
    transcript_text = '\n'.join(
        f"{'MYM' if m['role'] == 'ai' else 'Student'}: {m['content']}"
        for m in transcript
    )

    prompt = (
        f"Below is a short conversation between a career exploration assistant (MYM) "
        f"and a student about {domain_label}.\n\n"
        f"---\n{transcript_text}\n---\n\n"
        f"Based on this conversation, generate exactly 3 brief personalized annotations "
        f"to display on the student's {domain_label} learning roadmap. Each annotation "
        f"should reference something specific the student said and connect it to a "
        f"learning step. Keep each annotation to 1 sentence (max 20 words).\n\n"
        f"Return ONLY a JSON array of 3 strings, no other text. Example:\n"
        f'["Since you enjoyed API design, start here.", "Your debugging instinct maps well to this step.", "Given your interest in security, pay extra attention here."]'
    )

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.5,
                max_output_tokens=300,
            ),
        )
        text = response.text.strip()
        # Strip markdown code fences if present
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        annotations = json.loads(text)
        if isinstance(annotations, list) and all(isinstance(a, str) for a in annotations):
            return annotations[:3]
    except Exception as e:
        logger.error(f"Gemini annotation generation failed: {e}")

    return []


# ─────────────────────────────────────────────────────────────────────────────
# Early termination heuristic (§9 / Phase 11)
# ─────────────────────────────────────────────────────────────────────────────


def has_sufficient_evidence(transcript):
    """
    Heuristic: after Turn 2 (3 user responses), check if the user has
    provided enough detail to skip Turn 3.

    Criteria: all user responses average >15 words and at least 2 are
    classified as 'substantive'.
    """
    user_messages = [m for m in transcript if m['role'] == 'user']
    if len(user_messages) < 2:
        return False

    word_counts = [len(m['content'].split()) for m in user_messages]
    avg_words = sum(word_counts) / len(word_counts)

    substantive_count = sum(
        1 for m in user_messages
        if classify_reply(m['content']) == 'substantive'
    )

    return avg_words > 15 and substantive_count >= 2


# ─────────────────────────────────────────────────────────────────────────────
# Structured Evidence Extraction (§10 / Phase 12)
# ─────────────────────────────────────────────────────────────────────────────


def extract_structured_evidence(transcript):
    """
    Prompt Gemini to extract structured evidence fields from the conversation.

    Returns a dict with keys: projects, technologies, responsibilities,
    problems_solved, motivations, strengths, gaps. Each is a list of strings
    (empty list if not mentioned).
    """
    transcript_text = '\n'.join(
        f"{'MYM' if m['role'] == 'ai' else 'Student'}: {m['content']}"
        for m in transcript
    )

    prompt = (
        f"Below is a conversation between a career exploration assistant (MYM) "
        f"and a student.\n\n"
        f"---\n{transcript_text}\n---\n\n"
        f"Extract structured evidence from what the STUDENT said (not MYM). "
        f"Return a JSON object with exactly these keys, each mapping to a list of "
        f"short strings (empty list if not mentioned):\n\n"
        f'{{\n'
        f'  "projects": [],\n'
        f'  "technologies": [],\n'
        f'  "responsibilities": [],\n'
        f'  "problems_solved": [],\n'
        f'  "motivations": [],\n'
        f'  "strengths": [],\n'
        f'  "gaps": []\n'
        f'}}\n\n'
        f"Return ONLY the JSON object, no other text."
    )

    empty = {
        'projects': [], 'technologies': [], 'responsibilities': [],
        'problems_solved': [], 'motivations': [], 'strengths': [], 'gaps': [],
    }

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=400,
            ),
        )
        text = response.text.strip()
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        result = json.loads(text)
        if isinstance(result, dict):
            # Ensure all expected keys exist
            for key in empty:
                if key not in result:
                    result[key] = []
            return result
    except Exception as e:
        logger.error(f"Gemini evidence extraction failed: {e}")

    return empty


def generate_insight_summary(domain, evidence, transcript):
    """
    Generate a concise insight summary that separates user-stated info
    from assessment observations.

    Returns a string summary. Persisted to DeepDiveChat.insight_summary.
    """
    domain_label = DOMAIN_LABELS.get(domain, domain)

    transcript_text = '\n'.join(
        f"{'MYM' if m['role'] == 'ai' else 'Student'}: {m['content']}"
        for m in transcript
    )

    evidence_summary = json.dumps(evidence, indent=2) if evidence else '{}'

    prompt = (
        f"You are summarising a deep-dive conversation about {domain_label}.\n\n"
        f"Conversation:\n{transcript_text}\n\n"
        f"Extracted evidence:\n{evidence_summary}\n\n"
        f"Write a concise 3–4 sentence summary in two parts:\n"
        f"1. **What you told us**: Key things the student explicitly shared "
        f"(projects, technologies, interests).\n"
        f"2. **What we observed**: Patterns from their assessment behavior "
        f"that align with or complement what they said.\n\n"
        f"Write in second person ('you'). Be warm and specific. "
        f"Do NOT use bullet points — write flowing sentences."
    )

    try:
        client = _get_client()
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.6,
                max_output_tokens=250,
            ),
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini insight summary failed: {e}")

    return ''
