# Bugfix Requirements Document

## Introduction

The Lemonmaxx AI backend currently uses an architecture where the LLM generates executable OpenUI pseudo-code directly as text. This code then passes through a fragile regex cleanup pipeline (`clean_ai_response`, `normalize_openui_response`, `clean_openui_response`), a component name validator (`validate_openui`), and finally reaches the frontend for execution. This architecture is the root cause of several recurring production failures: the model hallucinates invalid component names (e.g. `completion()`, `COUNT()`, `running()`), regex patterns break on edge cases, escaping errors corrupt the output, and invalid components slip through validation. Additionally, the LLM generating full OpenUI code takes 6–10 seconds versus 1–3 seconds for structured JSON output.

The fix replaces the LLM-generates-code path with a two-step approach: the LLM returns strict structured JSON (validated via Pydantic), and a deterministic Python backend renderer converts that JSON into valid OpenUI syntax. This eliminates hallucinated components, removes all regex cleanup, and reduces latency.

---

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the LLM generates an OpenUI response containing a hallucinated component name (e.g. `completion()`, `COUNT()`, `running()`) THEN the system passes it through regex cleanup and validation, which either fails to catch it or produces a generic fallback error UI instead of a useful response.

1.2 WHEN the LLM response contains edge-case string content (e.g. quotes, backslashes, newlines inside component arguments) THEN the system's regex-based `clean_ai_response()` and `normalize_openui_response()` functions corrupt or drop parts of the response.

1.3 WHEN the LLM returns a response that does not contain `root =` (e.g. a plain text explanation or partial output) THEN the system wraps it in a generic `build_fallback_openui()` TextContent card, discarding the actual AI-generated content.

1.4 WHEN the LLM generates OpenUI code with a variable referenced before it is defined THEN the system silently drops the unreferenced variable, producing an incomplete or broken UI without surfacing an error.

1.5 WHEN the LLM generates a response that takes 6–10 seconds to produce full OpenUI pseudo-code THEN the system delivers a slow response to the user, degrading the experience.

1.6 WHEN the frontend receives and executes AI-generated pseudo-code strings THEN the system exposes a reliability and security risk because the executed code originates from an untrusted LLM output rather than a validated backend structure.

### Expected Behavior (Correct)

2.1 WHEN the LLM is asked to generate a UI response THEN the system SHALL instruct the LLM to return strict structured JSON conforming to a Pydantic schema, making hallucinated component names structurally impossible.

2.2 WHEN the LLM returns structured JSON THEN the system SHALL validate it with a Pydantic model and reject any response that does not conform to the schema, returning a typed validation error instead of silently corrupting output.

2.3 WHEN the validated JSON is available THEN the system SHALL pass it to a deterministic Python backend renderer that generates valid OpenUI syntax without any regex cleanup step.

2.4 WHEN the backend renderer generates OpenUI syntax THEN the system SHALL produce output that only uses components from the known-valid `ALLOWED_COMPONENTS` set, making invalid component names impossible by construction.

2.5 WHEN the LLM returns a structured JSON response THEN the system SHALL complete the LLM call in 1–3 seconds, reducing end-to-end latency compared to the current 6–10 second OpenUI code generation.

2.6 WHEN the frontend receives the final response THEN the system SHALL deliver pre-rendered, backend-validated OpenUI syntax rather than raw AI-generated executable code, eliminating the security and reliability risk of frontend code execution of LLM output.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the user sends a greeting or simple chitchat message THEN the system SHALL CONTINUE TO respond with a simple TextContent card without calling any data tools.

3.2 WHEN the user asks an analytics question THEN the system SHALL CONTINUE TO call `get_live_campaign_insights` (or equivalent data tools), pass the results to the AI layer, and return a rendered UI response containing the data.

3.3 WHEN the LangGraph workflow routes a message to an agent (analytics, campaigns, automations, reporting, rejected_ads, general) THEN the system SHALL CONTINUE TO route correctly and invoke the appropriate agent node.

3.4 WHEN the post-processor node runs THEN the system SHALL CONTINUE TO produce a final `openui_response` string stored in `AgentState` that the `/api/v1/ai/chat` endpoint returns in the `ChatResponse`.

3.5 WHEN the AI response pipeline fails at any stage THEN the system SHALL CONTINUE TO return a fallback error UI (using `error_ui()` or equivalent) rather than raising an unhandled exception to the client.

3.6 WHEN the WebSocket streaming endpoint receives a message THEN the system SHALL CONTINUE TO stream response chunks to the client and send a final `done` event with the complete processed response.

3.7 WHEN conversation memory context is available THEN the system SHALL CONTINUE TO include prior conversation history in the LLM request to maintain conversational continuity.

3.8 WHEN the `save_message_memory` function is called after a response THEN the system SHALL CONTINUE TO persist both the user message and the AI response to the conversation memory store.

3.9 WHEN the analytics builder (`build_analytics_ui`) is called with campaign data THEN the system SHALL CONTINUE TO produce a valid OpenUI response containing a summary, a campaign table, and optionally a chart.

3.10 WHEN the fallback components (`error_ui`, `loading_ui`, `empty_ui`) are invoked THEN the system SHALL CONTINUE TO return valid OpenUI strings using only allowed components.
