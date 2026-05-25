# Pipeline -- App Specification
**Hackathon Draft v0.1 | May 25, 2026**

---

## Overview

Pipeline is an AI-first office assistant for skilled trades small businesses. The core problem: owner-operators are working on job sites while potential customers are calling, texting, or emailing -- and not getting answered. Missed calls = lost revenue. Pipeline acts as a 24/7 AI intake agent that handles customer inquiries, triages urgency, offers appointment slots, and sends quotes -- so the tradesperson lands the job without stopping work.

**Demo scope:** Plumbing only. One trade, done well, is the right call for a 2-day build.

**App name:** Pipeline (deliberate double meaning: plumbing + sales pipeline / intake queue)

**Competitors (none are AI-native):** Jobber, ServiceTitan, Workiz

---

## Hackathon Judging Criteria Alignment

| Criterion | How Pipeline addresses it |
|---|---|
| Impact / usefulness | Solves a real, high-frequency revenue problem for a large underserved market |
| Technical execution | Agent orchestration, triage logic, invoice gen, CSV calendar, persistent storage |
| Demo quality | Three scripted scenarios with a live chat UI and contractor dashboard |
| Novelty / creativity | AI-native from the ground up; no existing product does this end-to-end |
| Shipping mindset | Scoped hard: one trade, text-first, CSV calendar, three demo scenarios |

---

## Demo Scenarios (use these to script the walkthrough)

Three scenarios must work end-to-end for the demo:

1. **Emergency** -- "Water is spraying everywhere, my basement is flooding." Agent detects emergency, escalates immediately, prompts contractor alert, offers to stay on the line for first steps.
2. **Routine service** -- "My hot water tank stopped working." Agent gathers details, checks availability from CSV, offers appointment window, sends quote via email.
3. **Scheduled work** -- "I need my dishwasher reinstalled." Agent scopes the job, collects contact info, books a slot, confirms via email.

---

## Mandatory MVP Features

### F1 -- AI Customer Intake Agent (Text Chat)

The primary interface for the hackathon. Customers interact with the agent via a text chat UI.

- Agent greets the customer and identifies itself as an AI assistant (never pretends to be human)
- Asks short, plumbing-specific triage questions -- not a generic FAQ bot
- Responses must be concise: short sentences, no essays, conversational pacing
- Conversation is stateful within a session (remembers context)
- Collects: customer name, contact info (phone + email), description of problem, any relevant details

### F2 -- Urgency Triage

The agent must distinguish between emergency and non-emergency requests and route accordingly.

- Detects explicit emergency signals ("flooding", "water everywhere", "no heat", "gas smell")
- Detects implicit urgency from tone or description
- Emergency path: notifies contractor immediately (notification mechanism TBD -- at minimum a flagged entry in dashboard), offers interim first-step advice ("turn off the water main")
- Non-emergency path: proceeds to scheduling and quoting flow

### F3 -- Availability and Scheduling (CSV Calendar)

The contractor pre-loads a CSV file representing their available appointment windows. The agent reads this and offers slots to the customer.

- CSV format: date, start time, end time, slot label (e.g., "morning", "afternoon")
- Agent offers up to 3 available windows to the customer
- Customer selects a slot; agent confirms
- Slot is marked as tentatively booked in the system (basic state management)
- **Optional / V2:** Real Google Calendar integration via a dedicated Google account

### F4 -- Quote and Invoice Generation

After scoping the job via conversation, the agent generates a structured quote.

- Quote includes: job description, estimated scope, estimated cost range, contractor name/contact, disclaimer that final price is confirmed on-site
- Quote is formatted clearly (not a wall of text)
- Invoice template is available post-job (same structure, with actual amounts)
- **Delivery:** Quote is emailed to the customer at the email address collected during intake

### F5 -- Email Delivery

- Agent asks for and captures customer email address during intake
- Sends quote/confirmation email to customer at end of conversation
- Email includes: appointment slot, job summary, what to expect, contractor contact info
- Email is triggered automatically -- no manual step by the contractor

### F6 -- RAG Knowledge Base (Plumbing Domain)

The agent uses a curated knowledge base to answer plumbing-specific questions accurately and stay in scope.

- Knowledge base seeded from a public plumbing resource (scraped for hackathon purposes; production use requires permission)
- Covers: common plumbing problems, what questions to ask per scenario, typical cost ranges, urgency indicators
- RAG retrieval keeps responses grounded and avoids hallucination on trade-specific details
- The knowledge base also drives the triage question set per scenario type

### F7 -- Contractor Dashboard ("The Pipeline")

A simple web view the contractor opens to see their incoming inquiries and current status.

- List of all incoming conversations with: customer name, timestamp, problem summary, urgency flag, status
- Status values: New, In Progress, Quoted, Booked, Closed
- Each row expandable to show full conversation transcript and generated quote
- Emergency-flagged entries are visually distinct (e.g., red badge)
- Dashboard updates in near-real time (polling acceptable for hackathon)
- No login/auth required for demo -- single contractor view

---

## Optional Features (out of scope for hackathon, noted to support architecture decisions)

These are intentionally deferred. They informed design choices (e.g., keeping text as the base layer under voice, keeping channels modular) but are not built.

| Feature | Notes |
|---|---|
| Voice channel (inbound call, speech-to-text / text-to-speech) | Text is the base layer. Voice is a wrapper. Architecture should not preclude adding it. 11 Labs or similar for TTS quality. Low-latency model selection is a constraint. |
| Real Google Calendar integration | Replace CSV with live Google Calendar read/write via a dedicated contractor account |
| Inbound email channel | Customer emails info@[contractor].com, agent processes and responds |
| Photo / image intake | Customer texts or sends a photo of the problem. WhatsApp API or SMS MMS. Agent acknowledges and routes to contractor. |
| Multi-trade support | Configuration layer that swaps out the RAG knowledge base and triage question set per trade (electrician, HVAC, carpenter, etc.) |
| Contractor onboarding questionnaire | 20-question setup flow that generates the contractor's custom FAQ and seeds the RAG |
| Multi-channel (WhatsApp, SMS) | Extend text chat to WhatsApp Business API or Twilio SMS |
| Analytics / conversion dashboard | Track inquiry-to-booking conversion rate, response time, revenue influenced |
| Full invoice workflow | Post-job invoice with actual line items, sent to customer, tracked for payment status |
| Contractor mobile alert | Push notification or SMS to contractor phone when an emergency is triaged |

---

## Functional Requirements Summary

| ID | Requirement |
|---|---|
| FR-01 | The agent must identify itself as AI at the start of every conversation |
| FR-02 | The agent must ask plumbing-specific triage questions, not generic ones |
| FR-03 | The agent must classify urgency within the first 2-3 turns |
| FR-04 | Emergency conversations must be flagged and surfaced immediately in the dashboard |
| FR-05 | The agent must collect customer name, email, phone, and problem description before closing |
| FR-06 | The agent must offer available appointment slots from the loaded CSV |
| FR-07 | A quote must be generated and emailed to the customer before the conversation ends |
| FR-08 | All conversations must be persisted to the database |
| FR-09 | The contractor dashboard must display all conversations with status and urgency |
| FR-10 | Agent responses must be short and conversational -- no paragraph-length answers |
| FR-11 | Voice, customer will speak and get answered back both in text and speech |


---

## Non-Functional Requirements

| ID | Requirement | Notes |
|---|---|---|
| NFR-01 | Response latency | Agent must respond within 3 seconds for non-voice. No 30-second waits. |
| NFR-02 | Conversation quality | Short, natural responses. If it sounds like a press-1-for-billing IVR, it has failed. |
| NFR-03 | Persistence | All conversations, quotes, and emails stored in a lightweight database (SQLite acceptable for hackathon) |
| NFR-04 | Modularity | Text is the base. Voice, email, and SMS are channels layered on top. Do not couple channel to logic. |
| NFR-05 | RAG grounding | Agent must not fabricate plumbing facts. All domain claims should be retrievable from the knowledge base. |
| NFR-06 | Scoped LLM use | Use a lightweight/fast model for conversation. Reserve heavier reasoning for triage classification and quote generation if needed. |
| NFR-07 | No auth required for demo | Single contractor context. No login, no multi-tenant. Ship it. |
| NFR-08 | Graceful fallback | If the agent cannot answer a question, it must say so clearly and offer to have the contractor follow up -- not hallucinate an answer. |
| NFR-09 | CSV calendar format | Well-documented, simple format. Contractor can edit in Excel. |
| NFR-10 | Demo stability | The three scripted scenarios must work reliably. No live unknown inputs during the judged demo. |
| NFR-11 | Debug mode | We need a debug to analyse all the in and out of the agent |

---

## Architecture Notes (not prescriptive -- for team alignment)

We are working with GCP

- **Orchestrator:**  framework for session and thread management https://learn.microsoft.com/en-us/agent-framework/overview/?pivots=programming-language-python
- **Plumbing Knowledge** Knwoledge database with be provided in the context window or through function calling if needed
- **Persistence:** Google storage in JSON
- **Calendar:** CSV parsed at startup or on request; slot state tracked in DB
- **Email:** Transactional email via API (SendGrid, Resend, etc.). => generate a flat file for now, we are going to implement a smtp later
- **Dashboard:** Simple web UI 
- **LLM selection for reasoning and agent** Fast model for conversation loop; heavier call acceptable for quote generation (async). First version => we will work with openAI or GCP models
- **Tools for speech to text** We need specific model to translate speech to text and text to speech

 

---

## Out of Scope (explicitly not in this build)

- Authentication / multi-user / multi-contractor
- Payment processing
- Mobile app
- Any trade other than plumbing
- Real calendar integration (CSV is MVP)
- Compliance / legal disclaimer generation (add a static boilerplate)

---

## Open Questions for the Team

1. What email service are we using for quote delivery? (SendGrid, Resend, etc.)
2. What is the tech stack? (Python? Node? Framework?)
3. Who owns the RAG data sourcing -- do we scrape a site or hand-craft a knowledge base?
4. What is the chat UI? Custom build or embed an existing component?
5. How do we handle the emergency notification to the contractor for the demo -- dashboard flag only, or do we simulate a push?
6. Do we have a contractor persona / name for the demo? ("Steve's Plumbing" etc.)
