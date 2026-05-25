# Joe Deliverables Tracker

Owner: Joe
Last updated: 2026-05-25

This document tracks Joe's hackathon deliverables for Pipeline (TMLS Agentic
Hackathon). Pipeline is a text-first AI intake assistant for plumbing
businesses (Jill's Plumbing for the demo).

Joe owns four areas:

- **D3** — Dashboard and chat UI visuals / spec
- **E9** — Triage and urgency logic
- **E10** — Calendly scheduling logic
- **E11** — Quote generation and approval flow

Each section below lists scope, deliverables, where the code/specs live,
acceptance criteria, and remaining TODOs.

---

## Product rules (recap)

These rules apply to everything below:

- MVP is **plumbing only**.
- MVP is **text-first** (in-app chat). No SMS, no voice.
- **Calendly** is the booking mechanism. No custom slot picker.
- **No Jill approval for appointment times.** The Calendly link goes straight
  to the customer; Jill sees the confirmed booking after.
- **Jill approval is required for quotes.**
- **Emergency** cases bypass normal quote/booking flow and alert Jill
  immediately.
- All agent responses must be short, conversational, and safe.
- Notifications to Jill fire **in parallel** with quote/scheduling work; they
  are not a gate.
- A conversation can terminate cleanly with **no call to action** (wrong
  number, out of area, customer changed mind, out of scope, spam).

---

## D3 — Dashboard + Chat UI visuals / spec

**Status:** spec ready, frontend implementation pending (owned by E7/E8 team).

**Spec doc:** [`ui_wireframe_notes.md`](./ui_wireframe_notes.md)

### Scope

Spec the screens, components, and states that the frontend team needs in
order to implement the contractor (Jill) dashboard and the customer chat,
without ambiguity.

### Deliverables

- [x] Customer chat screen wireframe + states
- [x] Jill dashboard list wireframe
- [x] Conversation detail panel wireframe
- [x] Quote approval panel wireframe
- [x] Calendly booking state display
- [x] Status badges: `New`, `In Progress`, `Emergency`, `Priority`,
  `Scheduled`, `Quote Draft`, `Quote Approved`, `Quote Rejected`,
  `Calendly Link Sent`, `Booked`, `Manual Follow-up`, `Closed — No Action`
- [x] Empty / loading / error states for every surface
- [x] JSON contracts the components consume (matches E9 / E10 / E11 outputs)

### Acceptance criteria

- Frontend can implement screens without a design call.
- Every badge has a colour token and a JSON value that produces it.
- Each surface (chat, list, detail, quote panel, booking panel) has
  defined empty, loading, and error states.

### Remaining TODOs

- [ ] Frontend team picks a CSS approach (Tailwind vs inline styles). Out of
  scope for Joe.
- [ ] Real-time polling cadence for the dashboard (recommend 3–5s; final call
  with frontend team).
- [ ] Decide whether the "rate framing" clarification (see E9) shows as a
  chip / suggested-reply in the chat UI.

---

## E9 — Triage and urgency logic

**Status:** implemented (rules + LLM fallback) with tests.

**Code:** [`backend/app/services/triage.py`](../backend/app/services/triage.py)

**Tests:** [`backend/tests/test_triage.py`](../backend/tests/test_triage.py)

### Scope

Classify each inbound customer message into one of:

- `emergency` — active damage, safety risk, no water, gas smell, sewage
  backup, urgent language with confirmed damage.
- `priority` — uncomfortable / inconvenient but contained (no hot water,
  contained leak, toilet not working without flooding).
- `scheduled` — planned work (dishwasher reinstall, faucet replacement,
  renovation, flexible timing).

### Implementation summary

Hybrid classifier:

1. **Stage A — Rules.** Keyword and phrase matching. Hard emergency signals
   short-circuit immediately.
2. **Stage B — Clarification.** If the customer claims urgency without hard
   emergency signals, the orchestrator should ask the customer to choose
   between "earliest available (emergency rate)" and "standard appointment
   (regular rate)". The result of that exchange flips the
   `customer_claimed_emergency` and `active_damage_confirmed` flags on the
   next call.
3. **LLM fallback.** If no rules fire and an LLM client is provided, the
   classifier calls it. The function is dependency-injected so tests run
   fully offline.
4. **Safe default.** If no rules fire and no LLM is available, returns
   `priority` with low confidence. Never silently downgrades a real
   emergency; never blindly escalates ambiguous input.

### JSON contract returned

```json
{
  "urgency_level": "emergency",
  "urgency_label": "Emergency",
  "confidence": 0.92,
  "reason": "Customer reports active flooding in basement.",
  "recommended_action": "Alert Jill immediately and stop normal quote/booking flow.",
  "customer_facing_guidance": "If safe, turn off your main water valve. Jill has been alerted.",
  "requires_human_followup": true,
  "continue_normal_flow": false,
  "needs_clarification": false,
  "customer_claimed_emergency": true,
  "active_damage_confirmed": true,
  "classification_source": "rules",
  "matched_signals": ["basement flooding", "spraying everywhere"]
}
```

### Acceptance criteria

- Emergency stops normal flow (`continue_normal_flow = false`).
- Priority continues intake but is flagged
  (`continue_normal_flow = true`, `requires_human_followup = true`).
- Scheduled continues standard flow
  (`continue_normal_flow = true`, `requires_human_followup = false`).
- Emergency includes safe, short customer-facing guidance.
- Output is easy for frontend / dashboard to consume (flat JSON, no nested
  objects).
- Tests cover all three demo scenarios plus the safe-default and LLM
  fallback paths.

### Remaining TODOs

- [ ] Orchestrator (E2) integration: call `classify_urgency` on every turn,
  store the latest result on the conversation.
- [ ] Orchestrator decision: when `needs_clarification` is true, send the
  "earliest vs standard" question to the customer before continuing.
- [ ] Optional: swap in a real LLM client (OpenAI / Vertex) by passing it
  into `classify_urgency(... llm_client=...)`.

---

## E10 — Calendly scheduling logic

**Status:** implemented with tests.

**Code:** [`backend/app/services/scheduling.py`](../backend/app/services/scheduling.py)

**Tests:** [`backend/tests/test_scheduling.py`](../backend/tests/test_scheduling.py)

### Scope

Decide when and how to send the customer a Calendly link, and track the
booking lifecycle on the dashboard. There is **no Jill approval step for
appointment times**.

### Behaviour by urgency

| Urgency    | Calendly link sent? | Notes                                                                 |
|------------|--------------------|-----------------------------------------------------------------------|
| Emergency  | No                 | Bypass Calendly entirely. Alert Jill. Show safety guidance.           |
| Priority   | Yes (after intake) | Ask the customer to pick the **earliest available** slot.             |
| Scheduled  | Yes (after scoping)| Ask the customer to pick any slot that works.                         |
| Quote-then-appointment | Yes (after customer accepts quote) | Triggered by `should_offer_calendly_after_quote(quote)` from E11. |

### JSON contract returned

```json
{
  "booking_status": "link_sent",
  "booking_method": "calendly",
  "scheduling_url": "https://calendly.com/jills-plumbing/consultation",
  "instructions_to_customer": "Please choose the earliest available time that works for you.",
  "requires_jill_time_approval": false,
  "urgency_context": "priority",
  "notify_jill": true
}
```

### Booking states

- `not_started`
- `link_sent`
- `booked`
- `cancelled`
- `manual_follow_up`

### Env / config

- `CALENDLY_SCHEDULING_URL` — primary scheduling URL. Falls back to
  `https://calendly.com/jills-plumbing/consultation` if unset.
- `CALENDLY_EVENT_TYPE_URI` — optional, only needed if/when we add the
  Calendly v2 event-type APIs.

### Acceptance criteria

- Appointment-only path can send a Calendly link.
- Quote-then-appointment path can send a Calendly link.
- Emergency path **does not** send a Calendly link
  (`booking_method == "manual_emergency"`).
- No Jill approval exists for appointment times
  (`requires_jill_time_approval` is always `false`).
- Dashboard can display `link_sent`, `booked`, `cancelled`,
  `manual_follow_up`.

### Remaining TODOs

- [ ] Wire the Calendly webhook (`invitee.created`, `invitee.canceled`) to
  call `mark_booked()` / `mark_cancelled()`. Owned by backend lead (E10
  webhook task in PROJECT_PLAN).
- [ ] Add the contractor's real Calendly URL to backend `.env` once the
  account is set up.

---

## E11 — Quote generation and approval

**Status:** implemented with tests.

**Code:** [`backend/app/services/quotes.py`](../backend/app/services/quotes.py)

**Tests:** [`backend/tests/test_quotes.py`](../backend/tests/test_quotes.py)

### Scope

Generate a quote draft from intake context, walk it through Jill approval,
deliver to the customer, then capture the customer's accept / decline so the
orchestrator knows whether to offer a Calendly link.

### Quote states

```
draft
  └─ pending_jill_review
       ├─ approved ─────────────► sent_to_customer ──► customer_accepted
       │                                          └─► customer_declined
       ├─ revision_requested ──► (back to draft, new version)
       └─ rejected               (terminal; manual follow-up on dashboard)
```

### JSON contract returned

```json
{
  "quote_status": "pending_jill_review",
  "job_summary": "Customer reports a leaking kitchen faucet.",
  "scope": [
    "Inspect faucet and supply lines",
    "Diagnose source of leak",
    "Repair or recommend replacement if needed"
  ],
  "estimated_price_range": "$150-$300",
  "disclaimer": "Final pricing will be confirmed on-site after inspection.",
  "requires_jill_approval": true,
  "version": 1,
  "history": [
    {"status": "draft", "note": null, "actor": "agent"},
    {"status": "pending_jill_review", "note": null, "actor": "agent"}
  ],
  "next_action": "Awaiting Jill review."
}
```

### Quote-to-booking flow

1. Intake collects enough context.
2. `generate_quote_draft(...)` returns a quote with status
   `pending_jill_review`.
3. Jill approves, revises (with a note), or rejects on the dashboard.
4. On approve, status becomes `sent_to_customer`; the orchestrator delivers
   it.
5. Customer accepts or declines.
6. On accept, `should_offer_calendly_after_quote(quote)` returns `True` and
   the orchestrator hands off to E10.

### Acceptance criteria

- Quote is not sent to the customer before Jill approval
  (`requires_jill_approval = true`, `quote_status != sent_to_customer` until
  Jill approves).
- Jill can approve, reject, or request revision with a note.
- Customer can accept or decline the quote.
- Customer acceptance triggers Calendly hand-off via
  `should_offer_calendly_after_quote`.
- Quote always includes the disclaimer that final pricing is confirmed
  on-site.

### Remaining TODOs

- [ ] Orchestrator (E2) wires quote generation when the customer's intent
  is "quote" or "quote-then-appointment".
- [ ] Dashboard (E7) renders the quote panel and the approve / revise /
  reject buttons per `ui_wireframe_notes.md`.
- [ ] Optional: swap rule-based quote drafting for an LLM call once the
  knowledge base (E6) is wired.

---

## Demo scenarios

Spec doc: [`demo_scenarios.md`](./demo_scenarios.md)

Three scripted scenarios drive the demo. All three must pass before the
judges' run.

| # | Scenario        | Urgency   | Calendly?              | Jill approval? |
|---|------------------|-----------|------------------------|----------------|
| 1 | Emergency        | emergency | No (bypass)            | Alert only     |
| 2 | Priority + quote | priority  | After customer accepts | Yes (quote)    |
| 3 | Scheduled        | scheduled | After scoping          | No             |

Each scenario in `demo_scenarios.md` includes the customer input, the exact
JSON each module returns, and the dashboard state at each step.

---

## Cross-cutting acceptance criteria

- All three demo scenarios run end-to-end through the modules.
- Every JSON output is flat and ready for direct dashboard rendering.
- The Calendly URL is environment-driven with a safe demo fallback.
- Emergency path never sends a Calendly link.
- Jill never approves appointment times.
- A "no call to action" close is a first-class terminal state on the
  dashboard.
- Pytest suite passes.

---

## Remaining TODOs (Joe's areas, rolled up)

- [ ] Wire Calendly webhook to `mark_booked()` / `mark_cancelled()` (with
  E10 backend lead).
- [ ] Orchestrator integration of `classify_urgency`, clarification turn,
  quote generation, and Calendly hand-off.
- [ ] Frontend implements D3 spec (E7 + E8 owners).
- [ ] Optional LLM wiring for triage + quote drafting.
- [ ] Replace fallback Calendly URL with Jill's real one in `.env`.
