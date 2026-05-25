"""E11 - Quote generation and approval.

Jill approval is required for quotes (unlike appointment times, which
go straight to the customer). The customer never sees a quote until
Jill has approved it.

Quote lifecycle states:

``draft`` -> ``pending_jill_review`` -> ``approved`` -> ``sent_to_customer``
                                     -> ``revision_requested`` (new draft)
                                     -> ``rejected`` (terminal)
``sent_to_customer`` -> ``customer_accepted`` | ``customer_declined``

For the hackathon we use rule-based templates keyed by ``problem_type``.
An LLM call can be swapped in later behind the same function signature.

All functions are pure: they return a new quote dict and never mutate the
input. ``history`` is appended to so the dashboard can render the audit
trail.
"""

from __future__ import annotations

from typing import Literal, Optional, TypedDict

QuoteStatus = Literal[
    "draft",
    "pending_jill_review",
    "approved",
    "revision_requested",
    "rejected",
    "sent_to_customer",
    "customer_accepted",
    "customer_declined",
]

JillDecision = Literal["approve", "revise", "reject"]
CustomerDecision = Literal["accept", "decline"]

Actor = Literal["agent", "jill", "customer"]


class HistoryEntry(TypedDict):
    status: str
    note: Optional[str]
    actor: Actor


class Quote(TypedDict):
    quote_status: QuoteStatus
    job_summary: str
    scope: list[str]
    estimated_price_range: str
    disclaimer: str
    requires_jill_approval: bool
    version: int
    history: list[HistoryEntry]
    next_action: str


DISCLAIMER = "Final pricing will be confirmed on-site after inspection."


# ---------------------------------------------------------------------------
# Templates keyed by problem_type. Easy to extend; unknown types fall back
# to ``default``.
# ---------------------------------------------------------------------------
_TEMPLATES: dict[str, dict] = {
    "leaking_faucet": {
        "scope": [
            "Inspect faucet and supply lines",
            "Diagnose source of leak",
            "Repair or recommend replacement if needed",
        ],
        "estimated_price_range": "$150-$300",
    },
    "hot_water_tank": {
        "scope": [
            "Inspect hot water tank and heating components",
            "Diagnose root cause (element, thermostat, gas valve, etc.)",
            "Repair or recommend replacement if needed",
        ],
        "estimated_price_range": "$250-$600",
    },
    "dishwasher_install": {
        "scope": [
            "Disconnect existing dishwasher (if present)",
            "Install and level new dishwasher",
            "Connect supply line and drain; leak test",
        ],
        "estimated_price_range": "$200-$400",
    },
    "clogged_drain": {
        "scope": [
            "Inspect affected drain",
            "Clear blockage using appropriate tools (snake, hydro-jet, etc.)",
            "Confirm flow restored and check for damage",
        ],
        "estimated_price_range": "$150-$350",
    },
    "toilet_repair": {
        "scope": [
            "Inspect toilet and connections",
            "Diagnose issue (flapper, fill valve, wax seal, etc.)",
            "Repair or replace components as needed",
        ],
        "estimated_price_range": "$150-$400",
    },
    "default": {
        "scope": [
            "On-site inspection",
            "Diagnose root cause",
            "Repair or recommend next steps",
        ],
        "estimated_price_range": "$150-$500",
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_quote_draft(
    *,
    job_summary: str,
    problem_type: str = "default",
    scope: Optional[list[str]] = None,
    estimated_price_range: Optional[str] = None,
) -> Quote:
    """Generate a fresh quote draft and immediately mark it pending Jill
    review.

    Args:
        job_summary: One-sentence summary of the customer's problem.
        problem_type: Key into the template table (e.g. ``"hot_water_tank"``).
            Falls back to ``"default"`` for unknown values.
        scope: Optional override for the scope bullets.
        estimated_price_range: Optional override for the price range
            string.
    """
    if not job_summary or not isinstance(job_summary, str):
        raise ValueError("job_summary must be a non-empty string")

    template = _TEMPLATES.get(problem_type, _TEMPLATES["default"])

    quote = Quote(
        quote_status="draft",
        job_summary=job_summary.strip(),
        scope=list(scope) if scope is not None else list(template["scope"]),
        estimated_price_range=estimated_price_range or template["estimated_price_range"],
        disclaimer=DISCLAIMER,
        requires_jill_approval=True,
        version=1,
        history=[{"status": "draft", "note": None, "actor": "agent"}],
        next_action="Submit to Jill for review.",
    )

    return _transition(
        quote,
        new_status="pending_jill_review",
        actor="agent",
        note=None,
        next_action="Awaiting Jill review.",
    )


def apply_jill_decision(
    quote: Quote,
    *,
    decision: JillDecision,
    note: Optional[str] = None,
) -> Quote:
    """Apply Jill's decision to a quote.

    - ``approve`` -> quote moves to ``approved`` then ``sent_to_customer``
      in one call. The history records both steps.
    - ``revise`` -> quote moves to ``revision_requested``; the orchestrator
      should call :func:`generate_quote_draft` again for the new version.
    - ``reject`` -> quote moves to ``rejected`` (terminal). Dashboard
      surfaces this for manual follow-up.
    """
    if quote.get("quote_status") != "pending_jill_review":
        raise ValueError(
            f"Jill can only decide on a quote in 'pending_jill_review' "
            f"(got {quote.get('quote_status')!r})"
        )

    if decision == "approve":
        approved = _transition(
            quote,
            new_status="approved",
            actor="jill",
            note=note,
            next_action="Send to customer.",
        )
        return _transition(
            approved,
            new_status="sent_to_customer",
            actor="agent",
            note=None,
            next_action="Awaiting customer response.",
        )

    if decision == "revise":
        return _transition(
            quote,
            new_status="revision_requested",
            actor="jill",
            note=note,
            next_action="Generate a new draft incorporating Jill's note.",
        )

    if decision == "reject":
        return _transition(
            quote,
            new_status="rejected",
            actor="jill",
            note=note,
            next_action="Surface on dashboard for manual follow-up.",
        )

    raise ValueError(
        f"decision must be 'approve', 'revise', or 'reject' (got {decision!r})"
    )


def apply_customer_decision(
    quote: Quote,
    *,
    decision: CustomerDecision,
) -> Quote:
    """Apply the customer's accept / decline decision to a quote.

    The customer can only decide on a quote in ``sent_to_customer``.
    """
    if quote.get("quote_status") != "sent_to_customer":
        raise ValueError(
            f"Customer can only decide on a quote in 'sent_to_customer' "
            f"(got {quote.get('quote_status')!r})"
        )

    if decision == "accept":
        return _transition(
            quote,
            new_status="customer_accepted",
            actor="customer",
            note=None,
            next_action="Offer Calendly link to book the job.",
        )
    if decision == "decline":
        return _transition(
            quote,
            new_status="customer_declined",
            actor="customer",
            note=None,
            next_action="Polite close; mark on dashboard.",
        )

    raise ValueError(
        f"decision must be 'accept' or 'decline' (got {decision!r})"
    )


def should_offer_calendly_after_quote(quote: Quote) -> bool:
    """Convenience hook: return ``True`` when the orchestrator should
    transition into the E10 Calendly flow."""
    return quote.get("quote_status") == "customer_accepted"


def start_revision(
    previous_quote: Quote,
    *,
    job_summary: Optional[str] = None,
    problem_type: str = "default",
    scope: Optional[list[str]] = None,
    estimated_price_range: Optional[str] = None,
) -> Quote:
    """Build a new draft from a quote that was sent back for revision.
    Bumps the version and copies the previous history forward so the
    dashboard shows the audit trail.
    """
    if previous_quote.get("quote_status") != "revision_requested":
        raise ValueError(
            "start_revision requires the previous quote to be in "
            "'revision_requested'"
        )

    template = _TEMPLATES.get(problem_type, _TEMPLATES["default"])
    new_version = int(previous_quote.get("version", 1)) + 1

    new_history: list[HistoryEntry] = list(previous_quote.get("history", []))
    new_history.append({"status": "draft", "note": None, "actor": "agent"})

    new_quote = Quote(
        quote_status="draft",
        job_summary=(job_summary or previous_quote["job_summary"]).strip(),
        scope=list(scope) if scope is not None else list(template["scope"]),
        estimated_price_range=estimated_price_range or template["estimated_price_range"],
        disclaimer=DISCLAIMER,
        requires_jill_approval=True,
        version=new_version,
        history=new_history,
        next_action="Submit revised draft to Jill for review.",
    )

    return _transition(
        new_quote,
        new_status="pending_jill_review",
        actor="agent",
        note=None,
        next_action="Awaiting Jill review (revised).",
    )


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


_VALID_TRANSITIONS: dict[QuoteStatus, set[QuoteStatus]] = {
    "draft": {"pending_jill_review"},
    "pending_jill_review": {"approved", "revision_requested", "rejected"},
    "approved": {"sent_to_customer"},
    "revision_requested": {"draft"},
    "rejected": set(),
    "sent_to_customer": {"customer_accepted", "customer_declined"},
    "customer_accepted": set(),
    "customer_declined": set(),
}


def _transition(
    quote: Quote,
    *,
    new_status: QuoteStatus,
    actor: Actor,
    note: Optional[str],
    next_action: str,
) -> Quote:
    current = quote.get("quote_status")
    allowed = _VALID_TRANSITIONS.get(current, set())  # type: ignore[arg-type]
    if new_status not in allowed:
        raise ValueError(
            f"Invalid quote transition: {current!r} -> {new_status!r}"
        )

    new_history: list[HistoryEntry] = list(quote.get("history", []))
    new_history.append({"status": new_status, "note": note, "actor": actor})

    return Quote(
        quote_status=new_status,
        job_summary=quote["job_summary"],
        scope=list(quote["scope"]),
        estimated_price_range=quote["estimated_price_range"],
        disclaimer=quote["disclaimer"],
        requires_jill_approval=quote["requires_jill_approval"],
        version=quote["version"],
        history=new_history,
        next_action=next_action,
    )
