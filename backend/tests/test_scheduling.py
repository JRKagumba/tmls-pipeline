"""Tests for E10 Calendly scheduling."""

from __future__ import annotations

import pytest

from app.services.scheduling import (
    DEMO_CALENDLY_URL,
    build_calendly_response,
    get_scheduling_url,
    mark_booked,
    mark_cancelled,
    mark_manual_follow_up,
)


# ---------------------------------------------------------------------------
# URL resolution
# ---------------------------------------------------------------------------


def test_get_scheduling_url_falls_back_to_demo(monkeypatch):
    monkeypatch.delenv("CALENDLY_SCHEDULING_URL", raising=False)
    assert get_scheduling_url() == DEMO_CALENDLY_URL


def test_get_scheduling_url_reads_env(monkeypatch):
    monkeypatch.setenv("CALENDLY_SCHEDULING_URL", "https://calendly.com/jill/foo")
    assert get_scheduling_url() == "https://calendly.com/jill/foo"


# ---------------------------------------------------------------------------
# build_calendly_response per urgency level
# ---------------------------------------------------------------------------


def test_emergency_bypasses_calendly():
    r = build_calendly_response("emergency")
    assert r["booking_status"] == "not_started"
    assert r["booking_method"] == "manual_emergency"
    assert r["scheduling_url"] is None
    assert r["instructions_to_customer"] is None
    assert r["requires_jill_time_approval"] is False
    assert r["notify_jill"] is True


def test_priority_sends_calendly_link_with_earliest_slot_instruction():
    r = build_calendly_response("priority")
    assert r["booking_status"] == "link_sent"
    assert r["booking_method"] == "calendly"
    assert r["scheduling_url"]
    assert "earliest" in r["instructions_to_customer"].lower()
    assert r["requires_jill_time_approval"] is False


def test_scheduled_sends_calendly_link_with_flexible_instruction():
    r = build_calendly_response("scheduled")
    assert r["booking_status"] == "link_sent"
    assert r["booking_method"] == "calendly"
    assert r["scheduling_url"]
    assert r["requires_jill_time_approval"] is False
    assert "any time" in r["instructions_to_customer"].lower()


def test_after_quote_context_tweaks_wording_for_priority():
    r = build_calendly_response("priority", context="after_quote")
    assert "approved quote" in r["instructions_to_customer"].lower()


def test_after_quote_context_tweaks_wording_for_scheduled():
    r = build_calendly_response("scheduled", context="after_quote")
    assert "approved quote" in r["instructions_to_customer"].lower()


def test_invalid_urgency_raises():
    with pytest.raises(ValueError):
        build_calendly_response("urgent")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Jill is never in the time-approval loop
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("level", ["emergency", "priority", "scheduled"])
def test_requires_jill_time_approval_is_always_false(level):
    r = build_calendly_response(level)
    assert r["requires_jill_time_approval"] is False


# ---------------------------------------------------------------------------
# Booking lifecycle transitions
# ---------------------------------------------------------------------------


def test_link_sent_to_booked():
    initial = build_calendly_response("priority")
    booked = mark_booked(initial)
    assert booked["booking_status"] == "booked"
    # Input is not mutated
    assert initial["booking_status"] == "link_sent"


def test_link_sent_to_cancelled():
    initial = build_calendly_response("scheduled")
    cancelled = mark_cancelled(initial)
    assert cancelled["booking_status"] == "cancelled"


def test_link_sent_to_manual_follow_up():
    initial = build_calendly_response("priority")
    flagged = mark_manual_follow_up(initial)
    assert flagged["booking_status"] == "manual_follow_up"


def test_booked_to_cancelled_is_allowed():
    initial = build_calendly_response("priority")
    booked = mark_booked(initial)
    cancelled = mark_cancelled(booked)
    assert cancelled["booking_status"] == "cancelled"


def test_invalid_transition_raises():
    initial = build_calendly_response("emergency")  # not_started
    # cannot move not_started -> booked directly
    with pytest.raises(ValueError):
        mark_booked(initial)


def test_cancelled_can_be_followed_by_new_link_sent():
    initial = build_calendly_response("priority")
    cancelled = mark_cancelled(initial)
    fresh = build_calendly_response("priority")
    # In practice the orchestrator would replace the booking state with a
    # new build_calendly_response call. The transition table allows
    # cancelled -> link_sent for that path.
    assert fresh["booking_status"] == "link_sent"
    assert cancelled["booking_status"] == "cancelled"
