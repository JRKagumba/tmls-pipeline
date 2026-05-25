"""Tests for E11 quote generation and approval."""

from __future__ import annotations

import pytest

from app.services.quotes import (
    DISCLAIMER,
    apply_customer_decision,
    apply_jill_decision,
    generate_quote_draft,
    should_offer_calendly_after_quote,
    start_revision,
)


# ---------------------------------------------------------------------------
# Quote draft generation
# ---------------------------------------------------------------------------


def test_generate_quote_draft_returns_pending_review():
    q = generate_quote_draft(
        job_summary="Hot water tank not producing heat.",
        problem_type="hot_water_tank",
    )
    assert q["quote_status"] == "pending_jill_review"
    assert q["requires_jill_approval"] is True
    assert q["disclaimer"] == DISCLAIMER
    assert q["estimated_price_range"] == "$250-$600"
    assert q["version"] == 1
    # History records both draft -> pending_jill_review
    statuses = [h["status"] for h in q["history"]]
    assert statuses == ["draft", "pending_jill_review"]


def test_generate_quote_draft_unknown_problem_uses_default_template():
    q = generate_quote_draft(
        job_summary="Some weird plumbing issue.",
        problem_type="something_unknown",
    )
    assert q["estimated_price_range"] == "$150-$500"
    assert q["scope"]


def test_generate_quote_draft_accepts_overrides():
    q = generate_quote_draft(
        job_summary="Custom job.",
        problem_type="default",
        scope=["Do the thing", "Verify the thing"],
        estimated_price_range="$999-$1000",
    )
    assert q["scope"] == ["Do the thing", "Verify the thing"]
    assert q["estimated_price_range"] == "$999-$1000"


def test_generate_quote_draft_requires_non_empty_summary():
    with pytest.raises(ValueError):
        generate_quote_draft(job_summary="", problem_type="default")


# ---------------------------------------------------------------------------
# Jill decisions
# ---------------------------------------------------------------------------


def test_jill_approve_auto_sends_to_customer():
    q = generate_quote_draft(
        job_summary="Leaking faucet.",
        problem_type="leaking_faucet",
    )
    approved = apply_jill_decision(q, decision="approve")
    assert approved["quote_status"] == "sent_to_customer"

    statuses = [h["status"] for h in approved["history"]]
    assert statuses == [
        "draft",
        "pending_jill_review",
        "approved",
        "sent_to_customer",
    ]


def test_jill_revise_moves_to_revision_requested():
    q = generate_quote_draft(
        job_summary="Leaking faucet.",
        problem_type="leaking_faucet",
    )
    revised = apply_jill_decision(
        q,
        decision="revise",
        note="Use a wider price range; could be the supply line.",
    )
    assert revised["quote_status"] == "revision_requested"
    last = revised["history"][-1]
    assert last["actor"] == "jill"
    assert last["note"] == "Use a wider price range; could be the supply line."


def test_jill_reject_is_terminal():
    q = generate_quote_draft(
        job_summary="Leaking faucet.",
        problem_type="leaking_faucet",
    )
    rejected = apply_jill_decision(q, decision="reject", note="Out of area.")
    assert rejected["quote_status"] == "rejected"

    # Can't move further from rejected
    with pytest.raises(ValueError):
        apply_jill_decision(rejected, decision="approve")


def test_jill_decision_requires_pending_state():
    q = generate_quote_draft(
        job_summary="Leaking faucet.",
        problem_type="leaking_faucet",
    )
    approved = apply_jill_decision(q, decision="approve")
    with pytest.raises(ValueError):
        apply_jill_decision(approved, decision="approve")


def test_invalid_jill_decision_raises():
    q = generate_quote_draft(
        job_summary="Leaking faucet.",
        problem_type="leaking_faucet",
    )
    with pytest.raises(ValueError):
        apply_jill_decision(q, decision="maybe")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Customer decisions
# ---------------------------------------------------------------------------


def test_customer_accept_triggers_calendly_hand_off():
    q = generate_quote_draft(
        job_summary="Hot water tank not producing heat.",
        problem_type="hot_water_tank",
    )
    q = apply_jill_decision(q, decision="approve")
    q = apply_customer_decision(q, decision="accept")
    assert q["quote_status"] == "customer_accepted"
    assert should_offer_calendly_after_quote(q) is True


def test_customer_decline_does_not_trigger_calendly():
    q = generate_quote_draft(
        job_summary="Hot water tank not producing heat.",
        problem_type="hot_water_tank",
    )
    q = apply_jill_decision(q, decision="approve")
    q = apply_customer_decision(q, decision="decline")
    assert q["quote_status"] == "customer_declined"
    assert should_offer_calendly_after_quote(q) is False


def test_customer_decision_requires_sent_to_customer():
    q = generate_quote_draft(
        job_summary="Leaking faucet.",
        problem_type="leaking_faucet",
    )
    with pytest.raises(ValueError):
        apply_customer_decision(q, decision="accept")


def test_invalid_customer_decision_raises():
    q = generate_quote_draft(
        job_summary="Leaking faucet.",
        problem_type="leaking_faucet",
    )
    q = apply_jill_decision(q, decision="approve")
    with pytest.raises(ValueError):
        apply_customer_decision(q, decision="ignore")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Revision cycle
# ---------------------------------------------------------------------------


def test_start_revision_bumps_version_and_carries_history():
    q = generate_quote_draft(
        job_summary="Leaking faucet.",
        problem_type="leaking_faucet",
    )
    q = apply_jill_decision(q, decision="revise", note="Bump price range.")
    revised = start_revision(
        q,
        problem_type="leaking_faucet",
        estimated_price_range="$200-$400",
    )
    assert revised["version"] == 2
    assert revised["quote_status"] == "pending_jill_review"
    assert revised["estimated_price_range"] == "$200-$400"
    # Previous history was carried forward
    statuses = [h["status"] for h in revised["history"]]
    assert "revision_requested" in statuses
    assert statuses[-1] == "pending_jill_review"


def test_start_revision_requires_revision_requested_state():
    q = generate_quote_draft(
        job_summary="Leaking faucet.",
        problem_type="leaking_faucet",
    )
    with pytest.raises(ValueError):
        start_revision(q)


# ---------------------------------------------------------------------------
# Immutability sanity check
# ---------------------------------------------------------------------------


def test_apply_jill_decision_does_not_mutate_input():
    q = generate_quote_draft(
        job_summary="Leaking faucet.",
        problem_type="leaking_faucet",
    )
    original_status = q["quote_status"]
    original_history_len = len(q["history"])
    _ = apply_jill_decision(q, decision="approve")
    assert q["quote_status"] == original_status
    assert len(q["history"]) == original_history_len
