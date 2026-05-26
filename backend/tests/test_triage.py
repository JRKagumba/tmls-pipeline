"""Tests for E9 triage classification."""

from __future__ import annotations

import pytest

from app.services.triage import classify_urgency


# ---------------------------------------------------------------------------
# Demo scenario coverage
# ---------------------------------------------------------------------------


def test_demo_scenario_1_emergency_basement_flooding():
    result = classify_urgency(
        "Water is spraying everywhere and my basement is flooding."
    )
    assert result["urgency_level"] == "emergency"
    assert result["continue_normal_flow"] is False
    assert result["requires_human_followup"] is True
    assert result["customer_facing_guidance"] is not None
    assert "main water valve" in result["customer_facing_guidance"]
    assert result["classification_source"] == "rules"
    assert result["needs_clarification"] is False
    assert result["active_damage_confirmed"] is True


def test_demo_scenario_2_priority_hot_water_tank():
    result = classify_urgency(
        "My hot water tank stopped working and I need someone soon."
    )
    assert result["urgency_level"] == "priority"
    assert result["continue_normal_flow"] is True
    assert result["requires_human_followup"] is True
    assert result["customer_facing_guidance"] is None
    assert result["classification_source"] == "rules"
    assert result["active_damage_confirmed"] is False
    assert result["customer_claimed_emergency"] is True


def test_demo_scenario_3_scheduled_dishwasher_next_week():
    result = classify_urgency(
        "I need my dishwasher reinstalled sometime next week."
    )
    assert result["urgency_level"] == "scheduled"
    assert result["continue_normal_flow"] is True
    assert result["requires_human_followup"] is False
    assert result["customer_facing_guidance"] is None
    assert result["classification_source"] == "rules"


# ---------------------------------------------------------------------------
# Emergency variants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "There's a burst pipe under the kitchen sink.",
        "I smell gas in the basement.",
        "I have no water in the home at all.",
        "There's sewage backing up into the tub.",
        "Water is near the electrical outlet on the wall.",
        "Pipe burst, water everywhere!",
    ],
)
def test_emergency_variants_classify_as_emergency(message):
    result = classify_urgency(message)
    assert result["urgency_level"] == "emergency", message
    assert result["continue_normal_flow"] is False
    assert result["customer_facing_guidance"]


def test_gas_smell_uses_gas_specific_guidance():
    result = classify_urgency("I smell gas in my kitchen.")
    assert result["urgency_level"] == "emergency"
    assert "911" in result["customer_facing_guidance"]


def test_water_near_electrical_uses_electrical_guidance():
    result = classify_urgency(
        "There's water pooling near the electrical panel in the basement."
    )
    assert result["urgency_level"] == "emergency"
    assert "breaker" in result["customer_facing_guidance"].lower()


# ---------------------------------------------------------------------------
# "no hot water" must NOT trigger the "no water" emergency rule
# ---------------------------------------------------------------------------


def test_no_hot_water_is_priority_not_emergency():
    result = classify_urgency("I have no hot water in the house.")
    assert result["urgency_level"] == "priority"


def test_no_water_is_emergency():
    result = classify_urgency("I have no water at all in the house.")
    assert result["urgency_level"] == "emergency"


# ---------------------------------------------------------------------------
# Priority variants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "The toilet won't flush.",
        "I have a small contained leak under the sink.",
        "The faucet has been dripping for a few days.",
        "We need someone today.",
        "Can you come this week? My hot water tank stopped working.",
    ],
)
def test_priority_variants_classify_as_priority(message):
    result = classify_urgency(message)
    assert result["urgency_level"] == "priority", message
    assert result["continue_normal_flow"] is True


# ---------------------------------------------------------------------------
# Scheduled variants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "Need a faucet replacement, no rush.",
        "We're renovating the kitchen and need plumbing done.",
        "I'd like to install a dishwasher whenever works for you.",
        "Looking to do a faucet install in a couple weeks.",
    ],
)
def test_scheduled_variants_classify_as_scheduled(message):
    result = classify_urgency(message)
    assert result["urgency_level"] == "scheduled", message
    assert result["continue_normal_flow"] is True
    assert result["requires_human_followup"] is False


# ---------------------------------------------------------------------------
# Soft-urgency-only: claims emergency but no hard signals.
# Should be priority + needs_clarification.
# ---------------------------------------------------------------------------


def test_soft_urgency_alone_is_priority_with_clarification():
    result = classify_urgency("I need help ASAP!")
    assert result["urgency_level"] == "priority"
    assert result["needs_clarification"] is True
    assert result["customer_claimed_emergency"] is True
    assert result["active_damage_confirmed"] is False
    assert result["classification_source"] == "rules"


def test_urgent_word_alone_is_priority_with_clarification():
    result = classify_urgency("This is urgent, please come right now.")
    assert result["urgency_level"] == "priority"
    assert result["needs_clarification"] is True


def test_hard_emergency_with_urgent_language_stays_emergency():
    result = classify_urgency(
        "Burst pipe in the basement, water everywhere, please come ASAP!"
    )
    assert result["urgency_level"] == "emergency"
    assert result["needs_clarification"] is False


# ---------------------------------------------------------------------------
# LLM fallback
# ---------------------------------------------------------------------------


def test_llm_fallback_when_no_rules_match():
    def fake_llm(message: str) -> dict:
        return {
            "urgency_level": "scheduled",
            "reason": "Customer asked an out-of-template scoping question.",
            "confidence": 0.7,
        }

    result = classify_urgency(
        "Hi, do you handle commercial plumbing inspections?",
        llm_client=fake_llm,
    )
    assert result["urgency_level"] == "scheduled"
    assert result["classification_source"] == "llm"
    assert "out-of-template" in result["reason"]


def test_llm_fallback_with_garbage_falls_back_to_safe_default():
    def garbage_llm(message: str) -> dict:
        return {"unexpected": "shape"}

    result = classify_urgency(
        "Hi, do you handle commercial plumbing inspections?",
        llm_client=garbage_llm,
    )
    assert result["urgency_level"] == "priority"
    assert result["classification_source"] == "safe_default"
    assert result["needs_clarification"] is True


def test_llm_exception_falls_back_to_safe_default():
    def broken_llm(message: str) -> dict:
        raise RuntimeError("API down")

    result = classify_urgency(
        "Hi, do you handle commercial plumbing inspections?",
        llm_client=broken_llm,
    )
    assert result["classification_source"] == "safe_default"
    assert result["urgency_level"] == "priority"


def test_llm_returns_non_dict_falls_back_to_safe_default():
    def string_llm(message: str) -> dict:
        return "emergency"  # type: ignore[return-value]

    result = classify_urgency(
        "Hi, do you handle commercial plumbing inspections?",
        llm_client=string_llm,
    )
    assert result["classification_source"] == "safe_default"


# ---------------------------------------------------------------------------
# Safe default when no rules and no LLM
# ---------------------------------------------------------------------------


def test_safe_default_when_no_rules_and_no_llm():
    result = classify_urgency("Hello, are you open on Saturdays?")
    assert result["urgency_level"] == "priority"
    assert result["confidence"] < 0.5
    assert result["classification_source"] == "safe_default"
    assert result["needs_clarification"] is True


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_non_string_message_raises():
    with pytest.raises(TypeError):
        classify_urgency(123)  # type: ignore[arg-type]


def test_history_widens_the_scan():
    result = classify_urgency(
        "Yes",
        history=["My basement is flooding right now"],
    )
    assert result["urgency_level"] == "emergency"
