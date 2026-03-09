---
name: chat_route
type: module
status: draft
dependencies:
  - ai_client
---

# Overview

Next.js App Router route handler for the `/api/chat` streaming endpoint.

# POST /api/chat — Route Handler

Next.js App Router route handler for a streaming AI chat endpoint.
Depends on `ai_client` for all LLM calls — never imports from `ai` directly.

## `POST(request)`

Accepts a JSON body `{ messages: Message[] }` and returns a streaming text response.

**Behaviour:**
1. Parse `messages` from the request JSON. If the array is empty or missing, return HTTP 400
   with body `{ error: "messages required" }`.
2. Call `streamChat(messages)` from `ai_client`.
3. Return a `StreamingTextResponse` wrapping the stream.
4. On error from `streamChat`, return HTTP 500 with body `{ error: "upstream error" }`.

**Returns:** `StreamingTextResponse` (200) or `Response` (400 / 500).

## Test Scenarios

| Scenario | Input | Expected |
|----------|-------|----------|
| Valid POST | `{ messages: [{role:"user", content:"Hi"}] }` | 200, streaming response |
| Empty messages | `{ messages: [] }` | 400, `{ error: "messages required" }` |
| Missing messages key | `{}` | 400, `{ error: "messages required" }` |
| Upstream error | `streamChat` throws | 500, `{ error: "upstream error" }` |
