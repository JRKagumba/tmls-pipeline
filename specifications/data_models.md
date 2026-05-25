# D1: Observability Models & External Library Reference

**Epic:** D1 | **Phase:** Design | **Date:** May 25, 2026

---

## MS Agent Framework — Native Types (do not re-implement)

These classes are provided by the MS Agent Framework SDK. Import and use them directly.
Downstream epics are listed so each team knows what to reach for.

### Sessions & State — used by E2, E4

| Class | Import | Key Fields | Notes |
|-------|--------|-----------|-------|
| `AgentSession` | `agents` | `session_id`, `state` (mutable dict) | Store conversation domain state in `state` (e.g. `state["conversation_id"]`, `state["status"]`, `state["urgency"]`). Supports `to_dict()` / `from_dict()` for persistence. |
| `BaseAgent` | `agents` | — | Subclass this to implement each sub-agent (Triage, Scheduling, QuoteGen, FAQ, Orchestrator) |

---

### Messages & Responses — used by E2, E3, E8

| Class | Import | Key Fields | Notes |
|-------|--------|-----------|-------|
| `Message` | `agents` | `role` (`"user"` \| `"assistant"`), `contents` (list of `Content`), `message_id`, `author_name` | One message in the conversation |
| `AgentResponse` | `agents` | `messages` (list of `Message`), `response_id`, `agent_id` | Non-streaming response from an agent run |
| `AgentResponseUpdate` | `agents` | `contents`, `role`, `message_id`, `response_id`, `agent_id` | Single streaming chunk |
| `ResponseStream` | `agents` | async iterator → `AgentResponseUpdate`; `.get_final_response()` → `AgentResponse` | Use for streaming to the chat UI |

---

### Content Types — used by E2, E9, E10, E11

All content is represented as a `Content` object created via factory methods.

| Factory method | Content type | Key fields | Used for |
|----------------|--------------|-----------|----------|
| `Content.from_text(text)` | `text` | `text` | Agent text responses |
| `Content.from_text_reasoning(text)` | `text_reasoning` | `text` | Chain-of-thought (debug only) |
| `Content.from_function_call(name, args)` | `function_call` | `function_name`, `arguments` (dict) | LLM requesting a tool call |
| `Content.from_function_result(result)` | `function_result` | `result` | Tool return value back to LLM |
| `Content.from_usage(...)` | `usage` | token counts, billing info | Captured in `ChatContext` for logging |
| `Content.from_error(code, details)` | `error` | `error_code`, `details` | Structured error responses |

---

### Middleware & Observability Hooks — used by E5

Attach middleware to intercept calls without modifying agent logic. All support `call_next()` for chaining.

| Middleware | Decorator | Context class | Intercepts | Key context fields |
|------------|-----------|--------------|------------|-------------------|
| Agent middleware | `@agent_middleware` | `AgentContext` | Full agent run (before + after) | `session`, `messages`, `options` |
| Chat middleware | `@chat_middleware` | `ChatContext` | Every LLM inference call | `chat_client`, `messages`, `options`, `result` |
| Function middleware | `@function_middleware` | `FunctionInvocationContext` | Every tool/function call | `function`, `arguments`, `result`, `session`, `metadata` |

> E5 implementation: wire `@agent_middleware` to write a `PipelineTurnLog` record per turn; wire `@chat_middleware` to log LLM request/response details; wire `@function_middleware` to log tool call inputs and outputs.

---

### Provider Options — used by E1, E2

| Class | When to use |
|-------|-------------|
| `OpenAIChatOptions` | If LLM decision = OpenAI. Pass as `default_options` to agent constructor. Fields: `model`, `temperature`, `max_tokens`, `response_format` |
| `VertexAIChatOptions` | If LLM decision = GCP Vertex AI / Gemini |

> Decision gate (from project plan): OpenAI vs GCP must be resolved before E2 starts.

---

## What We Define: PipelineTurnLog

The one custom record the logging layer (E5) writes per agent turn.
Captures pipeline-specific fields the framework has no concept of.

| Field | Type | Source |
|-------|------|--------|
| `id` | UUID string | Generated at turn start |
| `conversation_id` | UUID string | `AgentSession.state["conversation_id"]` |
| `turn_number` | int | `AgentSession.state["turn_number"]` (increment each turn) |
| `sub_agent` | `"conversation"` \| `"notification"` \| `"quote"` \| `"scheduling"` | Set by orchestrator before delegating |
| `routing_decision` | string | Short explanation of why this sub-agent was chosen |
| `state_before` | ConversationStatus | `AgentSession.state["status"]` read before turn |
| `state_after` | ConversationStatus | `AgentSession.state["status"]` read after turn |
| `latency_ms` | int | Wall-clock time for the full agent turn |
| `timestamp` | ISO 8601 | |

### ConversationStatus values
`New` → `Triaged` → `Scheduled` → `Quoted` → `Approved` → `Booked` → `Closed`

(Full state machine and transitions owned by the state machine team.)

---

## Epic → Data Objects Reference

Quick lookup for each implementing team. Business objects (Customer, Conversation, Quote, etc.) are excluded — see the state machine team's output for those.

| Epic | Objects needed | Notes |
|------|---------------|-------|
| **E1** Infrastructure | `OpenAIChatOptions` | LLM provider confirmed as OpenAI (per agent_design.mermaid) |
| **E2** Agent Architecture | `BaseAgent`, `AgentSession`, `Message`, `AgentResponse`, `ResponseStream`, `AgentResponseUpdate`, `Content.from_text()`, `Content.from_function_call()`, `Content.from_function_result()`, `OpenAIChatOptions` | Four sub-agents: `conversation`, `notification`, `quote`, `scheduling` — each subclasses `BaseAgent`; orchestrator manages `AgentSession.state` for routing |
| **E3** REST API | `AgentResponse`, `ResponseStream`, `AgentResponseUpdate`, `Message` | Serialize `AgentResponse.messages` to JSON for the `/chat` response; stream `AgentResponseUpdate` chunks if using SSE |
| **E4** Storage & Persistence | `AgentSession` (`to_dict()` / `from_dict()`) | Use built-in serialization to persist and restore session state to GCS (`interactions.json`, `quotes.json`) |
| **E5** Logging & Observability | `@agent_middleware` + `AgentContext`, `@chat_middleware` + `ChatContext`, `@function_middleware` + `FunctionInvocationContext`, `Content.from_usage()`, `PipelineTurnLog` (custom) | Wire all three middleware layers; `PipelineTurnLog` is the only custom schema to write |
| **E6** Knowledge Base | `Content.from_function_call()`, `Content.from_function_result()`, `Content.from_text()` | Plumbing knowledge included in system prompt (per agent_design.mermaid); tool call pattern used if KB grows beyond prompt window |
| **E7** Dashboard UI | None | Next.js frontend — consumes REST API JSON only, no direct framework dependency |
| **E8** Chat UI | `AgentResponseUpdate` (if streaming via SSE) | If non-streaming, just consume `AgentResponse` JSON from E3 API |
| **E9** Conversation Agent | `BaseAgent`, `AgentSession`, `Content.from_text()`, `Content.from_function_call()`, `Content.from_function_result()`, `Content.from_error()` | Handles full customer dialogue; continuously updates urgency (L1/L2/L3) in `AgentSession.state`; decides when to hand off to orchestrator |
| **E10** Scheduling Agent | `BaseAgent`, `AgentSession`, `Content.from_text()`, `Content.from_function_call()`, `Content.from_function_result()` | Sends Calendly link; receives webhook confirmation; slot state written to `AgentSession.state` |
| **E11** Quote Agent | `BaseAgent`, `AgentSession`, `Content.from_text()`, `Content.from_function_call()`, `Content.from_function_result()`, `Content.from_error()` | Generate → Jill review loop → email customer; quote ID written to `AgentSession.state` |
| **E12** Integration & Demo | All of the above | No new objects; validates that all epics wire together correctly |
