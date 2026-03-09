---
name: chat_ui
type: bundle
status: draft
dependencies:
  - ai_client
---

# Chat UI

Next.js App Router route handlers for a streaming AI chat interface. Depends on `ai_client`
for all LLM calls — never imports from `ai` directly.

## `POST /api/chat` — Route Handler

**File:** `src/app/api/chat/route.ts`

Accepts a JSON body `{ messages: Message[] }` and returns a streaming text response.

**Behaviour:**
1. Parse `messages` from the request JSON. If the array is empty or missing, return HTTP 400
   with body `{ error: "messages required" }`.
2. Call `streamChat(messages)` from `ai_client`.
3. Return a `StreamingTextResponse` (from the `ai` package) wrapping the stream.
4. On error from `streamChat`, return HTTP 500 with body `{ error: "upstream error" }`.

**Returns:** `StreamingTextResponse` (200) or `Response` (400 / 500).

## `useChatMessages()` — React Hook

**File:** `src/hooks/useChatMessages.ts`

Client-side hook managing the chat message list and streaming state.

**Returns:**
```typescript
{
  messages: Message[];          // current conversation
  isLoading: boolean;           // true while awaiting a stream chunk
  sendMessage: (text: string) => Promise<void>;  // appends user msg, streams reply
  clearMessages: () => void;    // resets to empty
}
```

**Behaviour of `sendMessage(text)`:**
1. Appends `{ role: "user", content: text }` to `messages`.
2. Sets `isLoading = true`.
3. POSTs to `/api/chat` with the updated messages array.
4. Reads the streamed response chunk by chunk, updating the last assistant message in real time.
5. Sets `isLoading = false` when the stream ends.
6. On network error, sets `isLoading = false` and appends an assistant message with content
   `"Sorry, something went wrong."`.

## Test Scenarios

| Scenario | Input | Expected |
|----------|-------|----------|
| Valid POST | `{ messages: [{role:"user", content:"Hi"}] }` | 200, streaming response |
| Empty messages | `{ messages: [] }` | 400, `{ error: "messages required" }` |
| Missing body | `{}` | 400, `{ error: "messages required" }` |
| Hook initial state | `useChatMessages()` | `messages=[], isLoading=false` |
| Hook sendMessage | call `sendMessage("Hello")` | appends user msg, sets isLoading |
