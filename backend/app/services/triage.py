"""E9 - Triage and urgency classification.

Hybrid classifier: rule-based pattern matching first, with optional LLM
fallback when no rules fire. Falls back to a safe ``priority`` default when
no rules match and no LLM is provided.

The classifier returns a flat dict ready for direct rendering on the
dashboard or further routing by the orchestrator.

Product rules baked in:

- Hard emergency signals (active damage, gas, no water, sewage backup)
  short-circuit to ``emergency``.
- Soft urgency words alone (``asap``, ``right now``, ``urgent``) without
  active damage do NOT escalate to emergency. They mark the result as
  ``needs_clarification`` so the orchestrator can ask the customer to
  pick between "earliest available (emergency rate)" and "standard
  appointment (regular rate)".
- Priority signals (no hot water, contained leak, toilet not working)
  classify as ``priority`` and continue normal flow.
- Scheduled signals (planned installs, "next week", "flexible") classify
  as ``scheduled``.
- We never produce DIY repair advice. The only customer-facing guidance
  is a short safety instruction on the emergency path.
"""

from __future__ import annotations

import re
from typing import Callable, Literal, Optional, TypedDict

UrgencyLevel = Literal["emergency", "priority", "scheduled"]
ClassificationSource = Literal["rules", "llm", "safe_default"]


class TriageResult(TypedDict):
    urgency_level: UrgencyLevel
    urgency_label: str
    confidence: float
    reason: str
    recommended_action: str
    customer_facing_guidance: Optional[str]
    requires_human_followup: bool
    continue_normal_flow: bool
    needs_clarification: bool
    customer_claimed_emergency: bool
    active_damage_confirmed: bool
    classification_source: ClassificationSource
    matched_signals: list[str]


# Optional callable: takes the customer message and returns a dict with at
# minimum {"urgency_level": "...", "reason": "..."}. Kept loose so the
# orchestrator can wire OpenAI / Vertex / MS Agent without coupling this
# module to any SDK.
LlmClient = Callable[[str], dict]


# ---------------------------------------------------------------------------
# Signal patterns
# ---------------------------------------------------------------------------

# Hard emergency patterns. Any match means: stop normal flow, alert Jill,
# show safety guidance. Each entry is (label, compiled regex).
#
# "no water" intentionally uses a negative lookbehind so it does NOT match
# "no hot water" (which is a priority signal, not an emergency).
_EMERGENCY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("basement flooding", re.compile(r"\bbasement\b.*\bflood(ing|ed)?\b|\bflood(ing|ed)?\b.*\bbasement\b", re.I)),
    ("flooding", re.compile(r"\bflood(ing|ed)\b", re.I)),
    ("spraying everywhere", re.compile(r"\bspraying\s+everywhere\b|\bwater\s+everywhere\b|\bspraying\s+water\b", re.I)),
    ("burst pipe", re.compile(r"\bburst\s+pipe(s)?\b|\bpipe\s+burst\b|\bpipe\s+exploded\b", re.I)),
    ("sewage backup", re.compile(r"\bsewage\s+back(ing|ed)?\s*up\b|\bsewer\s+back(ing|ed)?\s*up\b|\bsewage\b", re.I)),
    (
        "water near electrical",
        re.compile(r"\bwater\b.{0,30}\b(outlet|outlets|electrical|panel|breaker|breakers|wiring)\b", re.I),
    ),
    ("gas smell", re.compile(r"\b(smell(s|ing)?|smelt)\s+(of\s+)?gas\b|\bgas\s+smell\b|\bsmell(s|ing)?\s+like\s+gas\b", re.I)),
    # Whole-home water loss. Lookbehind prevents matching "no hot water".
    ("no water", re.compile(r"(?<!hot\s)\bno\s+water\b(?!\s+heater)", re.I)),
    ("cannot shut off water", re.compile(r"can'?t\s+shut\s+off\s+(the\s+)?water|main\s+valve\s+(broken|stuck|won'?t)", re.I)),
]

# Soft urgency phrases. By themselves they do NOT escalate to emergency
# (everyone claims urgency). They flip ``customer_claimed_emergency`` and
# trigger ``needs_clarification`` if no hard signal also matched.
_SOFT_URGENCY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("asap", re.compile(r"\basap\b", re.I)),
    ("right now", re.compile(r"\bright\s+now\b", re.I)),
    ("right away", re.compile(r"\bright\s+away\b", re.I)),
    ("immediately", re.compile(r"\bimmediately\b", re.I)),
    ("urgent", re.compile(r"\burgent(ly)?\b", re.I)),
    ("emergency word", re.compile(r"\bemergenc(y|ies)\b", re.I)),
    ("need someone soon", re.compile(r"\bneed\s+someone\s+(soon|today|now)\b|\bneed\s+help\s+(soon|today|now)\b", re.I)),
]

# Priority signals. Continue normal intake but flag for follow-up.
_PRIORITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("no hot water", re.compile(r"\bno\s+hot\s+water\b", re.I)),
    ("hot water tank stopped", re.compile(r"\bhot\s+water\s+(tank|heater)\b.*\b(stopped|broken|not\s+working|died|out)\b", re.I)),
    ("hot water not working", re.compile(r"\bhot\s+water\b.*\bnot\s+working\b", re.I)),
    ("contained leak", re.compile(r"\b(contained|small|minor|slow)\s+leak\b|\bleak\b.*\b(contained|not\s+spreading)\b", re.I)),
    ("dripping", re.compile(r"\b(dripping|drip)\b", re.I)),
    ("slow drain getting worse", re.compile(r"\bslow\s+drain\b.*\b(worse|worsening|backing\s+up)\b|\bdrain\b.*\b(getting\s+worse|backing\s+up)\b", re.I)),
    ("toilet not working", re.compile(r"\btoilet\b.*\b(not\s+working|won'?t\s+flush|broken|clogged)\b", re.I)),
    ("within 24 48 hours", re.compile(r"\bwithin\s+(24|48|24-48|24\s*to\s*48)\s*hours?\b", re.I)),
    ("today or tomorrow", re.compile(r"\b(today|tomorrow)\b", re.I)),
    ("this week", re.compile(r"\bthis\s+week\b", re.I)),
]

# Scheduled signals. Planned, flexible timing.
_SCHEDULED_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("dishwasher reinstall", re.compile(r"\bdishwasher\b.*\b(reinstall|install|hook(\s|-)?up)\b|\b(reinstall|install)\b.*\bdishwasher\b", re.I)),
    ("faucet replacement", re.compile(r"\b(replace|replacement|new|install)\b.*\bfaucet\b|\bfaucet\b.*\b(replace|replacement|install)\b", re.I)),
    ("planned install", re.compile(r"\bplanned\s+install(ation)?\b|\bnew\s+install(ation)?\b", re.I)),
    ("renovation", re.compile(r"\b(renovat\w*|remodel\w*|reno)\b", re.I)),
    ("next week", re.compile(r"\bnext\s+week\b|\bin\s+a\s+(few|couple)\s+weeks?\b", re.I)),
    ("flexible", re.compile(r"\bflexible\b|\bno\s+rush\b|\bwhenever\s+(you|works|is\s+convenient)\b|\bwhen\s+convenient\b", re.I)),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_urgency(
    message: str,
    history: Optional[list[str]] = None,
    *,
    llm_client: Optional[LlmClient] = None,
) -> TriageResult:
    """Classify a customer message into ``emergency``, ``priority``, or
    ``scheduled``.

    Args:
        message: The latest customer message.
        history: Optional list of prior customer messages, used to widen
            the text the rules scan over.
        llm_client: Optional callable invoked when no rules match. It
            must accept a single string (the message) and return a dict.
            If the dict is malformed, the function falls back to the safe
            default.

    Returns:
        A flat ``TriageResult`` dict.
    """
    if not isinstance(message, str):
        raise TypeError("message must be a string")

    haystack = message
    if history:
        haystack = "\n".join(history) + "\n" + message

    emergency_hits = _match(_EMERGENCY_PATTERNS, haystack)
    priority_hits = _match(_PRIORITY_PATTERNS, haystack)
    scheduled_hits = _match(_SCHEDULED_PATTERNS, haystack)
    soft_urgency_hits = _match(_SOFT_URGENCY_PATTERNS, haystack)

    customer_claimed_emergency = bool(emergency_hits or soft_urgency_hits)

    # 1. Hard emergency: any hard signal wins.
    if emergency_hits:
        return _build_emergency_result(emergency_hits)

    # 2. Scheduled wins over priority only when no priority signals fire.
    if scheduled_hits and not priority_hits and not soft_urgency_hits:
        return _build_scheduled_result(scheduled_hits)

    # 3. Priority: explicit priority signals.
    if priority_hits:
        return _build_priority_result(
            priority_hits + soft_urgency_hits,
            customer_claimed_emergency=customer_claimed_emergency,
            needs_clarification=bool(soft_urgency_hits),
        )

    # 4. Soft urgency only: classify as priority, but ask the customer to
    #    clarify (earliest vs standard appointment).
    if soft_urgency_hits:
        return _build_priority_result(
            soft_urgency_hits,
            customer_claimed_emergency=True,
            needs_clarification=True,
            soft_only=True,
        )

    # 5. Scheduled, no priority, no soft urgency: clean scheduled.
    if scheduled_hits:
        return _build_scheduled_result(scheduled_hits)

    # 6. No rules fired. Try LLM if provided.
    if llm_client is not None:
        llm_result = _call_llm_safely(llm_client, message)
        if llm_result is not None:
            return llm_result

    # 7. Safe default: priority, low confidence, ask for follow-up.
    return _safe_default_result()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _match(
    patterns: list[tuple[str, re.Pattern[str]]],
    text: str,
) -> list[str]:
    """Return the labels of every pattern that matches ``text``."""
    return [label for label, pat in patterns if pat.search(text)]


def _confidence_from_hits(n: int, *, cap: float = 0.95, base: float = 0.75) -> float:
    """Crude confidence scaling: more matched signals = higher confidence,
    capped to leave room for an LLM-graded result to exceed."""
    if n <= 0:
        return 0.0
    return min(cap, base + 0.08 * (n - 1))


def _build_emergency_result(signals: list[str]) -> TriageResult:
    # Two specific guidance lines, picked by signal type. Keep short and
    # safe. Never DIY repair advice.
    guidance = "If safe, turn off your main water valve. Jill has been alerted."
    if any("gas" in s for s in signals):
        guidance = (
            "Please leave the area, do not use any electrical switches, "
            "and call 911 if you suspect a gas leak. Jill has been alerted."
        )
    elif any("electrical" in s or "water near electrical" in s for s in signals):
        guidance = (
            "If safe, turn off power at your breaker panel and stay away "
            "from any water near outlets. Jill has been alerted."
        )

    reason_parts = ", ".join(signals[:3])
    return TriageResult(
        urgency_level="emergency",
        urgency_label="Emergency",
        confidence=_confidence_from_hits(len(signals), cap=0.95, base=0.85),
        reason=f"Detected emergency signal(s): {reason_parts}.",
        recommended_action="Alert Jill immediately and stop normal quote/booking flow.",
        customer_facing_guidance=guidance,
        requires_human_followup=True,
        continue_normal_flow=False,
        needs_clarification=False,
        customer_claimed_emergency=True,
        active_damage_confirmed=True,
        classification_source="rules",
        matched_signals=signals,
    )


def _build_priority_result(
    signals: list[str],
    *,
    customer_claimed_emergency: bool,
    needs_clarification: bool,
    soft_only: bool = False,
) -> TriageResult:
    reason_parts = ", ".join(signals[:3]) if signals else "soft urgency language"
    if soft_only:
        reason = (
            f"Customer used urgent language ({reason_parts}) but no active "
            "damage signals detected."
        )
        action = (
            "Ask customer to choose earliest-available (emergency rate) or "
            "standard appointment (regular rate)."
        )
    else:
        reason = f"Detected priority signal(s): {reason_parts}."
        action = "Continue intake and offer earliest Calendly slot or quote."

    return TriageResult(
        urgency_level="priority",
        urgency_label="Priority",
        confidence=_confidence_from_hits(len(signals), cap=0.9, base=0.75),
        reason=reason,
        recommended_action=action,
        customer_facing_guidance=None,
        requires_human_followup=True,
        continue_normal_flow=True,
        needs_clarification=needs_clarification,
        customer_claimed_emergency=customer_claimed_emergency,
        active_damage_confirmed=False,
        classification_source="rules",
        matched_signals=signals,
    )


def _build_scheduled_result(signals: list[str]) -> TriageResult:
    reason_parts = ", ".join(signals[:3])
    return TriageResult(
        urgency_level="scheduled",
        urgency_label="Scheduled",
        confidence=_confidence_from_hits(len(signals), cap=0.92, base=0.8),
        reason=f"Detected scheduled-work signal(s): {reason_parts}.",
        recommended_action="Continue scoping then send Calendly link.",
        customer_facing_guidance=None,
        requires_human_followup=False,
        continue_normal_flow=True,
        needs_clarification=False,
        customer_claimed_emergency=False,
        active_damage_confirmed=False,
        classification_source="rules",
        matched_signals=signals,
    )


def _safe_default_result() -> TriageResult:
    return TriageResult(
        urgency_level="priority",
        urgency_label="Priority",
        confidence=0.4,
        reason="No emergency, priority, or scheduled signals detected; routing to priority for human follow-up.",
        recommended_action="Ask one or two scoping questions, then re-classify.",
        customer_facing_guidance=None,
        requires_human_followup=True,
        continue_normal_flow=True,
        needs_clarification=True,
        customer_claimed_emergency=False,
        active_damage_confirmed=False,
        classification_source="safe_default",
        matched_signals=[],
    )


# Whitelist of fields we will accept from an LLM response. Anything else
# is discarded.
_LLM_ALLOWED_LEVELS: set[UrgencyLevel] = {"emergency", "priority", "scheduled"}


def _call_llm_safely(llm_client: LlmClient, message: str) -> Optional[TriageResult]:
    """Call the LLM and coerce its output into a valid ``TriageResult``.

    Returns ``None`` if the LLM raises, returns a non-dict, or returns an
    unrecognised urgency level. Callers should fall back to the safe
    default in that case.
    """
    try:
        raw = llm_client(message)
    except Exception:
        return None

    if not isinstance(raw, dict):
        return None

    level = raw.get("urgency_level")
    if level not in _LLM_ALLOWED_LEVELS:
        return None

    reason = str(raw.get("reason") or "LLM classification.")
    confidence = float(raw.get("confidence") or 0.6)
    confidence = max(0.0, min(0.99, confidence))

    if level == "emergency":
        return TriageResult(
            urgency_level="emergency",
            urgency_label="Emergency",
            confidence=confidence,
            reason=reason,
            recommended_action="Alert Jill immediately and stop normal quote/booking flow.",
            customer_facing_guidance="If safe, turn off your main water valve. Jill has been alerted.",
            requires_human_followup=True,
            continue_normal_flow=False,
            needs_clarification=False,
            customer_claimed_emergency=True,
            active_damage_confirmed=True,
            classification_source="llm",
            matched_signals=[],
        )
    if level == "priority":
        return TriageResult(
            urgency_level="priority",
            urgency_label="Priority",
            confidence=confidence,
            reason=reason,
            recommended_action="Continue intake and offer earliest Calendly slot or quote.",
            customer_facing_guidance=None,
            requires_human_followup=True,
            continue_normal_flow=True,
            needs_clarification=bool(raw.get("needs_clarification", False)),
            customer_claimed_emergency=bool(raw.get("customer_claimed_emergency", False)),
            active_damage_confirmed=False,
            classification_source="llm",
            matched_signals=[],
        )
    return TriageResult(
        urgency_level="scheduled",
        urgency_label="Scheduled",
        confidence=confidence,
        reason=reason,
        recommended_action="Continue scoping then send Calendly link.",
        customer_facing_guidance=None,
        requires_human_followup=False,
        continue_normal_flow=True,
        needs_clarification=False,
        customer_claimed_emergency=False,
        active_damage_confirmed=False,
        classification_source="llm",
        matched_signals=[],
    )
