# Pipeline Project Plan - Epic-Level Breakdown

**Build Duration:** 2 days (Hackathon)  
**Last Updated:** May 25, 2026  
**Status:** Planning Phase  
**Target:** ~17 high-level epics, max 60 tasks total (14 implementation + 3 design)

---

## Workflow: Design Phase → Implementation Phase

### Phase 1: Design Alignment (Day 1, Hours 0–2) — All epics in parallel
- **D1:** Domain, Data & Observability Models
- **D2:** API & System Architecture  
- **D3:** Dashboard & Chat UI Design

### Phase 2: Implementation (Day 1, Hours 2–7 + Day 2, All) — Parallel by team
- **E1–E14:** Core systems build

---

## Epic Summary (Design + Implementation)

| Epic # | Epic Title | Owner | Type | Dependencies | Day | Hours |
|--------|-----------|-------|------|--------------|-----|-------|
| **D1** | Domain, Data & Observability Models | Mateen | Design | None | D1 | 1–1.5 |
| **D2** | API & System Architecture | Jen / Emeric | Design | None | D1 | 1–1.5 |
| **D3** | Dashboard & Chat UI Design | Calan | Design | None | D1 | 1–1.5 |
| **E1** | Infrastructure & DevOps Setup | Emeric | Impl | None | D1 | 1–1.5 |
| **E2** | Agent Architecture Implementation | Calan | Impl | D2, E1 | D1 | 1–2 |
| **E3** | REST API Implementation (FastAPI) | Backend Lead | Impl | D2, E1 | D1–2 | 2.5–3 |
| **E4** | Backend Storage & Persistence | Storage Lead | Impl | D1, E1 | D1 | 2.5–3 |
| **E5** | Logging, Debug & Observability | DevOps/Backend | Impl | D1, E1 | D1 | 1.5–2 |
| **E6** | Knowledge Base & Domain Logic | Product/Domain Lead | Impl | E1 | D1 | 1.5–2 |
| **E7** | Dashboard UI Implementation | Frontend Lead | Impl | D3, E3 | D1–2 | 2–3 |
| **E8** | Chat UI Implementation | Frontend Lead | Impl | D3, E3 | D1–2 | 2–2.5 |
| **E9** | Triage & Urgency Logic | Joe / Calan | Impl | D2, E2, E6 | D1–2 | 1.5–2 |
| **E10** | Scheduling & Calendar Logic | Joe / Calan | Impl | D2, E2, E4 | D1–2 | 1.5–2 |
| **E11** | Quote Generation & Approval | Joe / Calan | Impl | D2, E2, E6 | D1–2 | 2–2.5 |
| **E12** | End-to-End Integration & Demo | QA/Integration Lead | Impl | All above | D2 | 3–4 |

---

## DESIGN PHASE (Day 1, Hours 0–2)

---

## DESIGN EPIC D1: Domain, Data & Observability Models

**Owner:** Mateen  
**Est. Time:** 1–1.5 hours  
**Blockers:** None  
**Deliverables:** Comprehensive data model doc. Object models (Pydantic/dataclasses). Storage schemas. Conversation state machine. Shared understanding across team. Jen owns business object modeling within D1 and shares sample quote/invoice examples.

| Task | Details | Est. |
|------|---------|------|
| **D1-1** | Design business domain entities: `Customer`, `Conversation`, `Quote`, `Booking`, `CalendarSlot`, `Message`, `Agent Turn`. Document relationships, required fields, validation rules. | 25 min |
| **D1-2** | Design JSON schemas for storage: `interactions.json` structure (sessions, messages, state), `quotes.json` structure (quotes, approvals, versions). Document versioning strategy. | 20 min |
| **D1-3** | Design observability object models: `AgentTurn`, `ConversationLog`, `ToolCall`, `LLMRequest`, `LLMResponse`. Fields for inputs, outputs, metadata, reasoning, latency, token counts, timestamps. | 20 min |
| **D1-4** | Design conversation state machine: states (New, Triaged, Scheduled, Quoted, Approved, Booked, Closed), transitions, terminal states. Diagram state flow. | 15 min |

**Deliverables:** 
- `data_models.md` — comprehensive entity definitions
- `storage_schema.yaml` — JSON file structures with examples
- `state_machine.txt` — state diagram
- **All team members understand:** what data flows where, what gets logged, how conversations evolve

**Acceptance:** Design doc reviewed by backend + frontend leads. No ambiguity on field names, types, or structures. Ready for implementation.

---

## DESIGN EPIC D2: API & System Architecture

**Owner:** Jen / Emeric  
**Est. Time:** 1–1.5 hours  
**Blockers:** None (but benefits from D1 review)  
**Deliverables:** OpenAPI spec. Endpoint contracts. Orchestration choreography. Error handling strategy. Ready for frontend to stub against.

| Task | Details | Est. |
|------|---------|------|
| **D2-1** | Design REST API contracts: endpoints (POST `/chat`, GET `/conversations`, GET `/conversations/{id}`, GET `/quotes/{id}`, POST `/quotes/{id}/review`), request/response payloads (using D1 models). | 25 min |
| **D2-2** | Design error handling & validation: HTTP status codes, error response format, validation rules, edge cases (empty input, timeout, invalid quote ID, etc.). | 20 min |
| **D2-3** | Design agent orchestration choreography: sub-agent call sequence (Triage → Scheduling → Quote Gen), data passed between agents, how state is maintained across turns. | 20 min |
| **D2-4** | Generate OpenAPI/Swagger spec document. Create mock endpoint examples. Document rate limits, session ID handling. | 15 min |

**Deliverables:** 
- `openapi.yaml` — full API spec (importable into Swagger UI)
- `orchestration_flow.txt` — agent choreography diagram
- `error_handling.md` — error codes, messages, client behavior
- **All team members understand:** what APIs exist, what they return, how agents talk to each other

**Acceptance:** OpenAPI spec can be imported into Swagger. Frontend can stub endpoints from spec. Backend understands agent orchestration flow. Zero ambiguity on request/response contracts.

---

## DESIGN EPIC D3: Dashboard & Chat UI Design

**Owner:** Calan  
**Est. Time:** 1–1.5 hours  
**Blockers:** None  
**Deliverables:** Wireframes/Figma. Component specs. Styling guide. Accessibility checklist. Ready for frontend implementation.

| Task | Details | Est. |
|------|---------|------|
| **D3-1** | Design dashboard layout: contractor view with conversation list (cards showing customer name, timestamp, problem summary, status badge, urgency badge in red for emergency), filter/search UI, conversation detail panel. Responsive mockups. | 30 min |
| **D3-2** | Design conversation detail view: message transcript, customer info card (name, phone, email), booked slot display, quote display (read-only + approve/reject/revise buttons), action buttons. | 20 min |
| **D3-3** | Design chat UI: customer-facing message list, input form, typing indicator, loading states, error messages, agent greeting. Responsive on mobile + desktop. | 20 min |
| **D3-4** | Design component library & styling: colors (emergency red, success green, neutral gray), typography, spacing, accessibility (contrast ratios, focus states). Create CSS framework or Tailwind config. | 15 min |

**Deliverables:** 
- Figma link (or equivalent design tool) with all screens
- `UI_COMPONENTS.md` — component specs (button sizes, card layouts, input styles)
- `ACCESSIBILITY.md` — WCAG compliance checklist, contrast ratios, keyboard nav
- `STYLE_GUIDE.md` — color palette, typography, spacing rules
- **All team members understand:** what the app looks like, user flows, brand guidelines

**Acceptance:** Design is pixel-perfect. Accessibility checklist passed. Frontend can start implementation without ambiguity. Design is cohesive (same colors, spacing, fonts across screens).

---

## IMPLEMENTATION PHASE (Day 1 Hours 2–7 + Day 2)

---

## EPIC E1: Infrastructure & DevOps Setup

**Owner:** Emeric  
**Est. Time:** 1.5 hours  
**Blockers:** None  
**Deliverables:** GCP project ready. Local dev env ready. All team members can clone and run code.

| Task | Details | Est. |
|------|---------|------|
| **E1-1** | GCP project setup, enable APIs (Cloud Storage), bucket creation | 20 min |
| **E1-2** | Python venv + base dependencies (FastAPI, uvicorn, GCS client, LLM SDK) | 15 min |
| **E1-3** | Git repo init, `.gitignore`, README with setup instructions | 10 min |
| **E1-4** | LLM decision (OpenAI vs GCP). Generate + secure API credentials in `.env.local` | 20 min |

**Acceptance:** `git clone`, `python -m venv venv`, install deps, FastAPI server starts on `localhost:8000`.

---

## EPIC E2: Agent Architecture Implementation

**Owner:** Calan  
**Est. Time:** 1.5–2 hours  
**Blockers:** E1, D2 (orchestration choreography)  
**Deliverables:** Sub-agent implementations. Orchestrator routing logic. Session management. MS Agent SDK integrated. Calan digitizes the whiteboard into a digital if/then/else prompt flow for E2 prompts.

| Task | Details | Est. |
|------|---------|------|
| **E2-1** | Implement MS Agent SDK setup + session/thread management | 20 min |
| **E2-2** | Implement Triage Sub-agent stub: accept input, classify urgency, return structured output per D2 spec | 30 min |
| **E2-3** | Implement Scheduling Sub-agent stub: accept input, offer slots, return structured output per D2 spec | 30 min |
| **E2-4** | Implement Quote Generator Sub-agent stub: accept input, generate quote object per D2 spec | 25 min |
| **E2-5** | Implement Main Orchestrator: routing logic per D2 choreography, conversation state machine per D1 design, manage session state | 25 min |

**Acceptance:** Orchestrator accepts message, routes to correct sub-agent, returns response. State machine transitions work. No LLM integration yet (stubs return placeholder responses).

---

## EPIC E3: REST API Implementation (FastAPI)

**Owner:** Backend Lead  
**Est. Time:** 2.5–3 hours  
**Blockers:** E1, D2 (API spec)  
**Deliverables:** FastAPI server with all endpoints working. Integrated with storage, logging, agent orchestrator, per D2 spec.

| Task | Details | Est. |
|------|---------|------|
| **E3-1** | FastAPI project skeleton: `main.py`, router structure, middleware for logging per D2 spec | 30 min |
| **E3-2** | Implement POST `/chat`: accept payload per D2 spec, call agent orchestrator (E2), return response per D2 schema | 45 min |
| **E3-3** | Implement GET `/conversations`, GET `/conversations/{id}`: fetch from storage per D1 schema, return per D2 spec | 30 min |
| **E3-4** | Implement GET `/quotes/{id}`, POST `/quotes/{id}/review`: quote retrieval and approval workflow per D2 spec | 30 min |
| **E3-5** | Wire endpoints to storage (E4), logging (E5), agent orchestrator (E2). End-to-end request → response. Error handling per D2 | 30 min |

**Acceptance:** All endpoints return correct JSON per D2 spec. Requests logged per D1/D5 observability models. No 500 errors on valid input. Error handling works.

---

## EPIC E4: Backend Storage & Persistence

**Owner:** Storage Lead  
**Est. Time:** 2.5–3 hours  
**Blockers:** E1, D1 (data models)  
**Deliverables:** Storage service. JSON/CSV handling. Google Storage integration. Data persists.

| Task | Details | Est. |
|------|---------|------|
| **E4-1** | Implement domain entity classes (Pydantic models from D1): `Customer`, `Conversation`, `Quote`, `Message`, etc. with validation | 30 min |
| **E4-2** | Implement storage service per D1 schema: `save_session()`, `get_session()`, `list_sessions()`, `save_quote()`, `get_quote()`. Serialize/deserialize to JSON. | 45 min |
| **E4-3** | Implement CSV calendar loader: parse calendar.csv, build `CalendarSlot` objects (D1 model), offer slots, tentatively reserve per D1 state machine | 30 min |
| **E4-4** | Integrate Google Cloud Storage client. Test sync to bucket. Verify data persists across restarts. | 20 min |

**Acceptance:** Write a session to storage, fetch it back. Data matches. Calendar slots work. State machine transitions persist.

---

## EPIC E5: Logging, Debug & Observability

**Owner:** DevOps / Backend Lead  
**Est. Time:** 1.5–2 hours  
**Blockers:** E1, D1 (observability models)  
**Deliverables:** Structured logging. Agent I/O capture. HTTP request logging. Queryable, readable logs.

| Task | Details | Est. |
|------|---------|------|
| **E5-1** | Implement domain entity classes for observability (D1): `AgentTurn`, `ConversationLog`, `ToolCall`, `LLMRequest`, `LLMResponse` with all fields | 30 min |
| **E5-2** | Implement `utils/logger.py`: structured JSON logging per D1 schema (request ID, timestamp, level, metadata, reasoning, latency) | 30 min |
| **E5-3** | Add FastAPI middleware for request/response logging + timing per D1 schema | 20 min |
| **E5-4** | Integrate logger into agent I/O: log every turn, every tool call, LLM requests/responses per D1 observability models | 15 min |

**Acceptance:** Every HTTP request logged per D1 schema. Every agent turn logged with inputs, outputs, metadata, latency. Logs are readable JSON, searchable by request ID.

---

## EPIC E6: Knowledge Base & Domain Logic

**Owner:** Product / Domain Lead  
**Est. Time:** 1.5–2 hours  
**Blockers:** E1  
**Deliverables:** Plumbing knowledge base (30–50 Q&As). Retrieval function. Integrated into agent prompts.

| Task | Details | Est. |
|------|---------|------|
| **E6-1** | Source plumbing knowledge: hand-craft or scrape 30–50 Q&As (emergency signals, common issues, cost ranges, triage Qs) | 45 min |
| **E6-2** | Format KB into structured format (YAML/JSON): `{ category, question, answer, keywords, urgency_level }` | 20 min |
| **E6-3** | Implement `services/knowledge_base.py`: keyword search, simple RAG retrieval | 20 min |
| **E6-4** | Integrate KB into agent system prompt. Test that agent grounds answers in KB. | 15 min |

**Acceptance:** Agent can retrieve relevant knowledge when asked a plumbing question. No hallucinations on facts.

---

## EPIC E7: Dashboard UI Implementation

**Owner:** Frontend Lead  
**Est. Time:** 2–3 hours  
**Blockers:** E3, D3 (UI design)  
**Deliverables:** Next.js dashboard. Conversation list + detail views. Quote approval UI. Real-time polling.

| Task | Details | Est. |
|------|---------|------|
| **E7-1** | Next.js project setup + layout per D3 design. Install styling (Tailwind or equivalent from D3). | 30 min |
| **E7-2** | Implement conversation list view per D3 design: fetch from `/conversations` (E3), display list, filter/search by status/customer, urgency badges (red for emergency) | 45 min |
| **E7-3** | Implement conversation detail view per D3 design: expand to show transcript, customer info, booked slot, quote, buttons | 30 min |
| **E7-4** | Implement quote approval UI per D3 design: approve/reject/revise buttons. POST to `/quotes/{id}/review` (E3). | 30 min |
| **E7-5** | Add real-time polling: fetch `/conversations` every 3–5 sec. Update UI on changes. | 20 min |

**Acceptance:** Dashboard loads per D3 design. Conversations visible. Click to expand → transcript. Approve button works. UI updates.

---

## EPIC E8: Chat UI Implementation

**Owner:** Frontend Lead (or co-owned with E7)  
**Est. Time:** 2–2.5 hours  
**Blockers:** E3, D3 (UI design)  
**Deliverables:** Customer chat UI. Message display + input. Session management. Integrated into Next.js.

| Task | Details | Est. |
|------|---------|------|
| **E8-1** | Chat component per D3 design: message list, input form, send button, typing indicator, loading states, error handling | 45 min |
| **E8-2** | Wire chat to POST `/chat` endpoint (E3): send user message, display agent response, handle errors per D2 error spec | 30 min |
| **E8-3** | Session management (frontend): create session on load, store session_id in localStorage, persist across reloads | 20 min |
| **E8-4** | Styling & accessibility per D3 guide: contrast, font sizes, mobile-responsive, keyboard nav, focus states | 20 min |

**Acceptance:** Customer can type message → see agent response. Conversation persists across reloads. Matches D3 design.

---

## EPIC E9: Triage & Urgency Logic

**Owner:** Joe / Calan  
**Est. Time:** 1.5–2 hours  
**Blockers:** E2, E6, D2 (orchestration)  
**Deliverables:** Triage sub-agent implementation. Emergency detection. Dashboard red badges for urgent convos.

| Task | Details | Est. |
|------|---------|------|
| **E9-1** | Implement Triage sub-agent: detect emergency signals (flooding, gas smell, no water, etc.). Classify urgency (CRITICAL/HIGH/NORMAL) per D1 state machine. Use KB (E6). | 45 min |
| **E9-2** | Test triage on demo scenarios: "Water everywhere" → CRITICAL, "Hot water tank" → NORMAL. Verify classification. | 30 min |
| **E9-3** | Ensure urgent conversations are flagged RED in dashboard (E7). Contractor sees immediate alert. | 20 min |

**Acceptance:** Triage reliably detects emergencies per D2 spec. Dashboard shows red badge per D3 design. Agent offers immediate first-step guidance.

---

## EPIC E10: Scheduling & Calendar Logic

**Owner:** Joe / Calan  
**Est. Time:** 1.5–2 hours  
**Blockers:** E2, E4, D1 (state machine)  
**Deliverables:** Scheduling sub-agent. CSV calendar parsing. Slot offer + reservation. Confirmation flow.

| Task | Details | Est. |
|------|---------|------|
| **E10-1** | Create sample CSV calendar per D1 schema: `date, start_time, end_time, label`. 3 days of slots. Document format. | 15 min |
| **E10-2** | Implement Scheduling sub-agent: offer all slots (urgent) or top 3 slots (non-urgent) per D2 orchestration spec. Format as readable options. | 40 min |
| **E10-3** | Implement slot selection: customer picks a slot. System tentatively reserves per D1 state machine. Return confirmation. | 30 min |
| **E10-4** | Test calendar flow: book slot in demo scenario 2 (routine) & 3 (scheduled). Verify state persists per D1 models. | 15 min |

**Acceptance:** Agent offers time slots. Customer selects one. Slot marked booked per D1 state machine. Dashboard shows booked time.

---

## EPIC E11: Quote Generation & Approval

**Owner:** Joe / Calan  
**Est. Time:** 2–2.5 hours  
**Blockers:** E2, E6, D1 (Quote model), D2 (API spec)  
**Deliverables:** Quote Generator sub-agent. Quote workflow. Approval flow. Email/file output. Jen shares sample quotes and invoices to inform quote formatting and pricing logic.

| Task | Details | Est. |
|------|---------|------|
| **E11-1** | Implement Quote Generator sub-agent: take job description + customer info, generate structured Quote object per D1 model | 45 min |
| **E11-2** | Store quote to storage (E4). Link to conversation per D1 schema. Display in dashboard (E7). | 30 min |
| **E11-3** | Implement contractor approval workflow: approve/reject/revise buttons per D3 UI design. Update quote status per D1 state machine. | 30 min |
| **E11-4** | Output approved quote: format as email-ready text/HTML. Write to flat file or prepare for SMTP. | 15 min |

**Acceptance:** Agent generates Quote per D1 model. Contractor approves via D3 UI. Quote status transitions per D1 state machine. Ready to email.

---

## EPIC E12: End-to-End Integration & Demo

**Owner:** QA / Integration Lead  
**Est. Time:** 3–4 hours  
**Blockers:** All above epics  
**Deliverables:** All 3 demo scenarios work end-to-end. Performance tested. Demo script + dry run.

| Task | Details | Est. |
|------|---------|------|
| **E12-1** | Run demo scenario 1 (Emergency): "Water everywhere" → agent detects per D1 triage, flags RED per D3 UI, offers first steps. Verify all components. | 45 min |
| **E12-2** | Run demo scenario 2 (Routine): "Hot water tank" → triage, book slot per D1 state machine, generate quote, contractor approves per D3 UI. | 45 min |
| **E12-3** | Run demo scenario 3 (Scheduled): "Dishwasher install" → triage, book, quote, approval. Full flow per D1 state machine. | 45 min |
| **E12-4** | Performance tuning: measure response latency (target < 3 sec per D2 spec). Refine prompts for conversational tone. Polish UI per D3. Fix blockers. | 60 min |
| **E12-5** | Write demo script. Dry run with team. Document exact inputs/expected outputs per D2 API spec. Final sign-off. | 30 min |

**Acceptance:** All 3 scenarios repeatable, stable, polished. No errors in logs. Demo is ready for judges.

---

## Dependencies & Parallelization

```
DESIGN PHASE (Day 1, Hours 0–2) — ALL IN PARALLEL:
  D1 (Data Models)          ──→ Unblocks E4, E5, E9, E10, E11
  D2 (API & Orchestration)  ──→ Unblocks E2, E3, E9, E11
  D3 (UI Design)            ──→ Unblocks E7, E8

INFRASTRUCTURE (Hour 1–2):
  E1 (Infrastructure)  ──→ Unblocks all implementation epics

IMPLEMENTATION PHASE (Hours 2–7 + Day 2) — PARALLEL BY TEAMS:
  
  Backend Track (can run parallel):
    E3 (API) depends on: E1, D2, E2, E4, E5
      └─ E4 (Storage) depends on: E1, D1
      └─ E5 (Logging) depends on: E1, D1
      └─ E9 (Triage) depends on: E2, E6, D2
      └─ E10 (Scheduling) depends on: E2, E4, D1
      └─ E11 (Quoting) depends on: E2, E6, D1, D2
  
  Frontend Track (can run parallel):
    E7 (Dashboard) depends on: E3, D3
    E8 (Chat UI) depends on: E3, D3
  
  Feature Logic (can run parallel):
    E2 (Agent) depends on: E1, D2
    E6 (Knowledge Base) depends on: E1
  
  Demo Phase (sequential):
    E12 (Integration & Demo) depends on: All above
```

---

## Time Estimation by Day

| Deliverable | Day 1 Target | Day 2 Target | Total |
|-------------|-------------|-------------|-------|
| **E1–E8** (Foundation + Design) | ✅ Complete | — | ~8 hours |
| **E2–E7, E9–E13** (Core Systems + Features) | ✅ Complete | — | ~20 hours |
| **E14** (Integration & Demo) | — | ✅ Complete | ~4 hours |
| **Buffer/Contingency** | — | ✅ Reserve | ~2 hours |

**Total:** ~34 hours of work across ~6–8 people, 2 days.

---

## Team Assignments (3 Design + 12 Implementation Epics for 8–10 People)

### Design Phase (Day 1, Hours 0–2) — All in parallel

| Epic | Owner | Start | End | Notes |
|------|-------|-------|-----|-------|
| **D1** | Data Architect | D1 Hr 0 | D1 Hr 1.5 | Data models, state machine, observability schema |
| **D2** | API Architect | D1 Hr 0 | D1 Hr 1.5 | API contracts, orchestration flow, error handling |
| **D3** | Design Lead | D1 Hr 0 | D1 Hr 1.5 | Dashboard, chat UI, component specs, styling |

### Implementation Phase (Day 1, Hours 2–7 + Day 2)

| Epic | Owner | Depends On | Start | End | Notes |
|------|-------|-----------|-------|-----|-------|
| **E1** | Platform Lead | None | D1 Hr 1.5 | D1 Hr 3 | Infrastructure first, unblocks all. |
| **E2** | Agent Architect | E1, D2 | D1 Hr 2 | D1 Hr 4 | Agent implementation per D2 choreography. |
| **E3** | Backend Lead | E1, D2 | D1 Hr 2 | D1 Hr 5 | API per D2 spec, integrates E2, E4, E5. |
| **E4** | Storage Lead | E1, D1 | D1 Hr 2 | D1 Hr 4.5 | Storage per D1 schema, entity models. |
| **E5** | DevOps/Backend | E1, D1 | D1 Hr 2 | D1 Hr 3.5 | Logging per D1 observability schema. |
| **E6** | Product/Domain | E1 | D1 Hr 2 | D1 Hr 3.5 | Knowledge base (independent). |
| **E7** | Frontend Lead | E3, D3 | D1 Hr 3 | D1 Hr 5.5 | Dashboard per D3 design, uses E3 API. |
| **E8** | Frontend Lead | E3, D3 | D1 Hr 3 | D1 Hr 5.5 | Chat UI per D3 design, parallel with E7. |
| **E9** | Agent/Backend | E2, E6, D2 | D1 Hr 3 | D1 Hr 4.5 | Triage logic, uses D2 spec. |
| **E10** | Backend Lead | E2, E4, D1 | D1 Hr 3.5 | D1 Hr 5 | Scheduling logic, per D1 state machine. |
| **E11** | Agent/Backend | E2, E6, D1, D2 | D1 Hr 4 | D1 Hr 6 | Quote generation, per D1 Quote model. |
| **E12** | QA/Integration | All above | D2 Hr 0 | D2 Hr 4 | End-to-end demo, perf tuning, dry run. |

---

## Recommended Team Composition (8–10 People)

**Design Phase (Hours 0–2):**
- **1 Data Architect** → D1 (creates data models, observability schema, state machine)
- **1 API Architect** → D2 (creates API spec, orchestration flow)
- **1 Design Lead** → D3 (creates UI/UX design, component specs)

**Implementation Phase (Hours 2–7 + Day 2):**
- **1 Platform/DevOps Lead** → E1, E5 (infrastructure + logging)
- **1 Backend Lead** → E3, E4, E10 (API, storage, scheduling)
- **1 Agent/AI Lead** → E2, E9, E11 (agent implementation, triage, quoting)
- **1 Product/Domain Lead** → E6 (knowledge base, domain logic)
- **1–2 Frontend Leads** → E7, E8 (dashboard + chat UI implementation)
- **1 QA/Integration Lead** → E12 (demo, integration, polish)

**Total: 3 designers (Day 1 Hrs 0–2) + 8 implementers (Day 1 Hrs 2–7 + Day 2). Designers can support implementation after Hour 2.**





---

## Daily Standup Checklist (Epic-Level)

### Day 1 Morning Kickoff (Hour 0)

- [ ] **D1, D2, D3 assigned** (design leads start immediately)
- [ ] **E1 assigned** (infrastructure starts immediately)
- [ ] Team aligned on decision gates: OpenAI vs GCP model, knowledge base approach, email MVP strategy
- [ ] All team members have repo access, can clone code

### Day 1 Mid-Morning Status (Hour 2)

- [ ] **D1, D2, D3 complete** ✅ (design phase done)
- [ ] **E1 complete or 80% done** ✅ (infrastructure ready)
- [ ] Designers transition to support roles (code review, answer questions)
- [ ] Implementation teams ready to start E2–E11

### Day 1 Noon Status (Hour 4)

- [ ] **E1 complete** ✅ (infrastructure ready)
- [ ] **E2, E4, E5, E6 at 50%+ done** (in progress)
- [ ] **E3, E7, E8 started** (API + frontend)
- [ ] **E9, E10, E11 queued or started** (depends on E2, E4 progress)
- [ ] Zero blockers on critical path

### Day 1 End-of-Day (Hour 7)

- [ ] **E1–E6 complete** (infrastructure, storage, logging, KB done)
- [ ] **E2, E3 at least 80% done** (agent + API mostly working)
- [ ] **E7, E8 at least 50% done** (frontend UI in progress)
- [ ] **E9, E10, E11 started or 50%+ done** (feature logic in progress)
- [ ] No blockers preventing Day 2 integration

### Day 2 Morning (Hour 0)

- [ ] **E2–E11 complete** (all implementations done, all features working)
- [ ] **E12 ready to begin** (integration lead takes over)

### Day 2 Noon (Hour 4)

- [ ] **E12-1, E12-2, E12-3 complete** (all 3 demo scenarios tested end-to-end)
- [ ] All scenarios repeatable and stable

### Day 2 End-of-Day (Hour 8)

- [ ] **E12-4, E12-5 complete** ✅ (performance tuned, demo script ready, dry run passed)
- [ ] No errors in logs. All three scenarios work reliably.
- [ ] **Ready to ship.**

---

## Recommended Work Cadence

### Day 1: Design First, Then Build

**Hours 0–2 (Design Phase — All in parallel):**
- **3 designers** work on D1, D2, D3 in parallel
- **1 DevOps** works on E1 (infrastructure) in parallel
- **At 2-hour mark:** Design complete, infrastructure ready, all teams aligned

**Hours 2–7 (Implementation Phase — Parallel tracks):**
- **Backend track:** E3, E4, E5 (core infrastructure)
- **Frontend track:** E7, E8 (dashboard, chat UI)
- **Agent track:** E2, E9, E11 (agent + logic)
- **Feature track:** E10, E6 (scheduling, KB)
- **All tracks:** leverage D1, D2, D3 designs + E1 infrastructure

**Day 1 Goal:** 
- ✅ D1–D3 complete (design locked)
- ✅ E1–E6 complete (infrastructure, storage, logging, KB)
- ✅ E2, E3 at 80%+ (agent + API mostly working)
- ✅ E7, E8 at 50%+ (frontend in progress)
- ✅ E9–E11 in progress (feature logic)

### Day 2: Integration & Polish

**Hours 0–3 (Finish Implementation):**
- Complete E2–E11 (any remaining work)
- Final QA checks

**Hours 3–6 (E12 Integration):**
- Run all 3 demo scenarios end-to-end
- Fix any integration issues
- Performance tuning

**Hours 6–8 (Polish & Demo Prep):**
- Dry run with team
- Final sign-off

**Day 2 Goal:**
- ✅ All 3 scenarios work reliably
- ✅ Performance: < 3 sec per turn
- ✅ Demo script rehearsed
- ✅ Ready for judges

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Customer / Contractor                    │
│   (Browser: /chat for customer, /dashboard for contractor)      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP(S)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js Frontend Server                       │
│  (/chat route, /dashboard route, static assets)                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │ API calls: /chat, /conversations, /quotes
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend Server                      │
│  (Routers: chat, conversations, quotes)                         │
│  (Middleware: logging, validation, error handling)              │
└──────────────┬────────────────────────────┬──────────────────────┘
               │                            │
               ▼ (orchestration)            ▼ (persistence)
     ┌─────────────────────┐      ┌──────────────────────┐
     │ MS Agent Framework  │      │ Storage Service      │
     │ - Orchestrator      │      │ - Google Storage GCS │
     │ - Sub-Agents        │      │ - Flat JSON files    │
     │   * Triage          │      │ - CSV calendar       │
     │   * Scheduling      │      └──────────────────────┘
     │   * Quote Gen       │
     │ - Session mgmt      │
     │ - LLM calls         │
     │   (OpenAI or GCP)   │
     └─────────────────────┘
           │ (knowledge base query)
           ▼
     ┌──────────────────┐
     │ Knowledge Base   │
     │ (Plumbing Q&As)  │
     └──────────────────┘
```

---

---

## Open Decisions (Blocking)

From spec, these must be decided before full build starts:

1. **LLM Choice:** OpenAI (GPT-4, GPT-4-turbo) or GCP (Vertex AI, Gemini)? → Task **INFRA-05**
2. **Knowledge Base Source:** Hand-craft Q&As or scrape public plumbing site? → Task **KB-01**
3. **Emergency Alert:** Dashboard flag only, or add simulated Slack/email to contractor? → Task **TRIAGE-04** (optional)
4. **Contractor Persona:** Use real name or placeholder? → Task **PERF-05** (impacts credibility)
5. **Email MVP:** Flat file output or wire SMTP? → Task **QUOTE-04** (file = safe, SMTP = nicer demo)

---

## Success Criteria

✅ **All three demo scenarios run end-to-end without manual intervention.**  
✅ **Agent responds in < 3 seconds per turn.**  
✅ **Conversations persist to storage and are visible in contractor dashboard.**  
✅ **Quotes are generated and contractor can approve/reject.**  
✅ **Emergency path (scenario 1) is visually distinct and alerts contractor immediately.**  
✅ **Code is clean, logged, and ready to hand off post-hackathon.**  
✅ **Team is confident to demo to judges with no surprises.**

---

## Appendix: Quick Reference

### Key File Locations (TBD)

```
tmls-pipeline/
├── backend/
│   ├── main.py                      # FastAPI app entry
│   ├── routers/
│   │   ├── chat.py                  # POST /chat
│   │   ├── conversations.py         # GET /conversations
│   │   └── quotes.py                # POST /quotes, GET /quotes/{id}
│   ├── models/
│   │   ├── schemas.py               # Pydantic models
│   │   └── domain.py                # Business logic models
│   ├── services/
│   │   ├── agent.py                 # Orchestrator + sub-agents
│   │   ├── storage.py               # Persistence layer
│   │   ├── knowledge_base.py         # KB retrieval
│   │   ├── calendar.py              # CSV calendar
│   │   └── quoting.py                # Quote generation (E13)
│   ├── utils/
│   │   └── logger.py                # Logging utility (E6)
│   └── requirements.txt             # Dependencies
│
├── frontend/
│   ├── pages/
│   │   ├── /chat.js                 # Customer chat (E10)
│   │   └── /dashboard.js            # Contractor dashboard (E9)
│   ├── components/
│   │   ├── ChatUI.js                # Chat component
│   │   ├── ConversationList.js      # Dashboard list
│   │   └── QuoteReview.js           # Quote approval
│   └── styles/
│       └── globals.css
│
├── data/
│   ├── calendar.csv                 # Sample availability slots
│   ├── knowledge_base.yaml          # Plumbing Q&As
│   └── contractor_profile.yaml      # "Steve's Plumbing" info
│
├── .env.local.example               # Template for secrets
├── .gitignore
├── README.md                        # Setup + run instructions
└── PROJECT_PLAN.md                  # This file
```

---

## What Gets Designed in Phase 1 (D1–D3)

### D1: Domain, Data & Observability Models
- **Business entities:** Customer, Conversation, Quote, Booking, CalendarSlot, Message, AgentTurn
- **Relationships:** How conversations link to quotes, how bookings reference calendar slots, etc.
- **Storage schemas:** JSON structure for persistence, versioning approach
- **Observability:** What gets logged (inputs, outputs, metadata, reasoning, latency, tokens)
- **State machine:** Conversation lifecycle (New → Triaged → Scheduled → Quoted → Booked → Closed)
- **Validation rules:** What makes a valid customer, quote, booking, etc.

**Why it matters:** All backend, storage, and logging teams use this single definition. No ambiguity on data flow.

---

### D2: API & System Architecture
- **REST API contracts:** Endpoints, request/response payloads, HTTP status codes
- **Error handling:** Standard error response format, error codes, what errors are possible
- **Agent orchestration:** Which sub-agents are called in what order, what data flows between them
- **State & session management:** How to maintain conversation state across turns
- **Rate limiting & throttling:** If needed

**Why it matters:** Frontend teams can stub endpoints immediately. Backend teams know exactly what to build. Zero guessing.

---

### D3: Dashboard & Chat UI Design
- **Contractor dashboard:** Layout, conversation list, detail view, filter/search, urgency badges (red for emergency)
- **Chat UI:** Customer-facing message display, input form, typing indicator, loading states, error handling
- **Component library:** Buttons, cards, inputs, modals — all with consistent styling
- **Accessibility:** Contrast ratios, keyboard navigation, focus states
- **Responsive design:** Mobile, tablet, desktop — all work

**Why it matters:** Frontend team has pixel-perfect reference. No rework. Designers can review implementation against spec.

---

## Decision Gates (Must Resolve Before Build Starts)

These decisions are **blocking** — resolve them before Day 1 Hour 1.

| Gate | Options | Impact | Owner | Target |
|------|---------|--------|-------|--------|
| **LLM Choice** | OpenAI (GPT-4, GPT-4-turbo) vs GCP (Vertex AI, Gemini) | Latency, cost, API style, prompt engineering | E1 Owner + D2 | D1 Hr 0.5 |
| **Knowledge Base Source** | Hand-craft 30–50 Q&As vs scrape public plumbing site | Time investment, control over content, accuracy | E6 Owner + D1 | D1 Hr 0.5 |
| **Email MVP** | Flat file output vs wire real SMTP/SendGrid | Demo polish, MVP scope, time budget | E11 Owner + D2 | D1 Hr 1 |
| **Emergency Alert Strategy** | Dashboard red badge only vs add simulated Slack/SMS | Demo impact, scope creep, judging criteria | E9 Owner + D3 | D1 Hr 1 |
| **Contractor Persona** | Use realistic "Steve's Plumbing, GTA" or placeholder | Credibility on stage, detail level | E12 Owner + D3 | D1 Hr 1 |

---

## Success Criteria (Definition of Done)

### Design Phase (D1–D3)
✅ **D1, D2, D3 complete within 2 hours. All team members reviewed + signed off.**  
✅ **Zero ambiguity on:** data models, API contracts, UI/UX design.  
✅ **Designers have communicated:** blockers, constraints, decisions to implementation teams.

### Implementation Phase (E1–E11)
✅ **All implementations follow D1–D3 designs without deviation.**  
✅ **E1–E6 complete by Hour 4 of Day 1.** (infrastructure, storage, logging, KB ready)  
✅ **E2, E3 at 80%+ by Hour 7 of Day 1.** (agent + API core working)  
✅ **E7–E11 at 50%+ by Hour 7 of Day 1.** (frontend + feature logic in progress)

### Integration & Demo (E12)
✅ **All three demo scenarios run end-to-end without manual intervention.**  
✅ **Agent responds in < 3 seconds per turn.**  
✅ **Conversations persist and are visible in dashboard (real-time polling).**  
✅ **Quotes are generated automatically. Contractor can approve/reject from dashboard.**  
✅ **Emergency path is visually distinct (red badge per D3 design) and alerts contractor immediately.**  
✅ **Code is logged per D1 observability schema. All agent I/O captured. Debuggable.**  
✅ **Repo is clean (no secrets, LLM keys in .env.local, not committed).**  
✅ **Team has rehearsed demo 2+ times. No surprises on stage.**

---

## Testing Checklist (Final E14)

### Scenario 1: Emergency
```
Input: "Water is spraying everywhere, my basement is flooding"
Expected Behavior:
  ✅ Agent recognizes emergency within first 2 turns
  ✅ Urgency = CRITICAL
  ✅ Dashboard conversation shows red badge
  ✅ Agent offers immediate first-step advice ("turn off water main")
  ✅ Contractor is notified (dashboard flag or alert)
  ✅ No quote generated (or marked as DRAFT pending contractor approval)
  ✅ Conversation persisted to storage
```

### Scenario 2: Routine Service
```
Input: "My hot water tank stopped working"
Expected Behavior:
  ✅ Agent asks follow-up questions (age, any noises, gas/electric, etc.)
  ✅ Urgency = NORMAL (not immediate emergency)
  ✅ Agent offers 3 available appointment slots
  ✅ Customer selects a slot (e.g., "Tuesday 2–4 PM")
  ✅ System tentatively books slot
  ✅ Agent generates quote (job: water tank repair/replacement, est. cost range)
  ✅ Contractor sees conversation + quote in dashboard
  ✅ Contractor approves quote
  ✅ Quote is ready to send to customer
  ✅ Entire flow takes < 5 minutes in real-time
```

### Scenario 3: Scheduled Work
```
Input: "I need my dishwasher reinstalled"
Expected Behavior:
  ✅ Agent gathers scope (current status, timeline preference, etc.)
  ✅ Urgency = NORMAL
  ✅ Agent offers 3 available slots
  ✅ Customer books slot
  ✅ Agent generates quote (job scope, estimated labor + parts, cost)
  ✅ Contractor reviews + approves quote
  ✅ Conversation status: New → In Progress → Quoted → Booked
  ✅ All data persists; dashboard updates in real-time
```

---

## Stretch Goals (If Time Permits)

If Day 2 integration finishes early:

- **SMS Channel (E15):** Add `/sms` endpoint. Simulated Twilio webhook. Route SMS to agent, respond back. ~1.5 hours.
- **Prompt Refinement UI (E16):** Contractor can edit agent prompts in dashboard. Changes take effect on next message. ~1 hour.
- **Analytics Dashboard (E17):** Show metrics: total inquiries, booking rate, avg response time. ~1.5 hours.
- **Multi-Trade Config (E18):** Load different knowledge bases + triage questions per trade (plumbing, electrical, HVAC). ~2 hours.

---

**Document Owner:** Project Lead  
**Last Updated:** May 25, 2026  
**Version:** Epic-Level (17 epics: 3 Design + 12 Implementation + 1 Integration, ~60 tasks)  
**Next Review:** Daily standup (start of each day)

---

## Design-First Approach: Why It Matters

### The Problem with Ad-Hoc Design
- Backend team builds API without frontend knowing endpoint contracts → rework
- Frontend team designs UI without backend constraints → incompatible layouts
- Agent team decides on state machine without storage team input → impedance mismatch
- Everyone guesses on data models → inconsistent field names, types, validations

### The Solution: Design Phase (D1–D3, Hours 0–2)

**All three design epics run in parallel. When complete, the entire team has:**
1. **Shared data model** (D1) — everyone speaks the same language about Customer, Conversation, Quote, etc.
2. **Locked API contract** (D2) — frontend can stub endpoints, backend knows exactly what to build
3. **Pixel-perfect UI spec** (D3) — frontend doesn't wonder "what should this look like?"

### Benefits for Team Communication

**Designers → Implementation Teams:**
- D1 Lead publishes: `data_models.md`, entity diagrams, state machine flow
- D2 Lead publishes: `openapi.yaml`, orchestration choreography, error codes
- D3 Lead publishes: Figma link, `UI_COMPONENTS.md`, `STYLE_GUIDE.md`, accessibility checklist
- **Team can now work independently without constant back-and-forth.**

**Implementation Teams → Designers (async feedback loop):**
- If E3 (Backend) discovers API needs adjustment → message D2, get async decision
- If E7 (Frontend) needs clarity on button styling → reference D3 spec, ask design lead if needed
- If E4 (Storage) needs to validate Quote model → use D1 spec as source of truth
- **Designers are available for questions but not blocking day-to-day coding.**

**Integration Lead (E12) → All Teams:**
- Uses D1 state machine to validate transitions
- Uses D2 API spec to verify endpoints return correct format
- Uses D3 design to QA UI pixel-perfect implementation
- **Dry run has zero surprises because everyone followed the same blueprint.**

---

## Key Alignment Documents (Deliverables from D1–D3)

| Epic | Deliverable | Format | Audience | Used By |
|------|------------|--------|----------|---------|
| **D1** | `data_models.md` | Markdown | All teams | E4, E5, E9, E10, E11, E12 |
| **D1** | Entity diagrams (Miro/Figma) | Visual | Backend, Storage | E4 implementation |
| **D1** | `state_machine.txt` | Diagram | All teams | E12 validation, acceptance testing |
| **D2** | `openapi.yaml` | OpenAPI 3.0 | Backend, Frontend | E3, E7, E8, E9–E11 |
| **D2** | Orchestration flow diagram | Miro/draw.io | Agent, Backend | E2, E9–E11 |
| **D2** | `error_handling.md` | Markdown | Backend, Frontend QA | E3, E7, E8, E12 |
| **D3** | Figma/design tool link | Design tool | Frontend, Designers | E7, E8, E12 |
| **D3** | `UI_COMPONENTS.md` | Markdown | Frontend | E7, E8 implementation |
| **D3** | `STYLE_GUIDE.md` | Markdown | Frontend, Design QA | E7, E8, E12 |
| **D3** | `ACCESSIBILITY.md` | Checklist | Frontend, QA | E7, E8, E12 validation |

---

## Communication During Implementation (Hours 2+)

### Daily Standup Pattern
**09:00 AM:** 5-min standup
- Any blockers on design?
- Any questions about D1/D2/D3?
- Any integration concerns?

**If blocker arises:**
- Async Slack: tag relevant design lead (designer available for quick decision)
- Designers prioritize blocking questions over design refinement
- Decision documented in appropriate design deliverable

### Integration Lead's Role (E12)
- Validates every implementation against design spec (D1–D3)
- Flags deviations: "This button doesn't match D3 spec" or "State machine transition missing per D1"
- Ensures no surprises at demo

---

## Why This Matters for a Hackathon

**Time is precious.** 
- Without design alignment: 20+ hours wasted on rework, back-and-forth, inconsistency
- With design alignment: 4–6 hours gained by knowing exactly what to build, how to build it, and how it all fits together

**Demo credibility.**
- Without design: Inconsistent UI, half-finished features, unclear state transitions → looks amateur
- With design: Pixel-perfect implementation, consistent brand, clear user flows → looks professional

**Team morale.**
- Without design: "I built this, but now I have to tear it down?" → frustration
- With design: "I know exactly what to build" → confidence, momentum, celebration when it works

---

**Design Phase is not overhead. It's the scaffolding that makes the build fast, parallel, and reliable.**

---

**Document Owner:** Project Lead  
**Last Updated:** May 25, 2026  
**Version:** Epic-Level (17 epics: 3 Design + 12 Implementation + 1 Integration, ~60 tasks)  
**Next Review:** Daily standup (start of each day)
