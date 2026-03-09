---
name: use_chat_messages
type: bundle
status: draft
dependencies:
  - ai_client
---

# `useChatMessages()` — React Hook

Client-side hook managing the chat message list and streaming state.
Communicates with the chat route handler via `fetch` to `/api/chat`.

## `useChatMessages()`

**Returns:**
```typescript
{
  messages: Message[];          // current conversation
  isLoading: boolean;           // true while awaiting a stream chunk
  sendMessage: (text: string) => Promise<void>;
  clearMessages: () => void;
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

**Behaviour of `clearMessages()`:** Resets `messages` to `[]`.

## Test Scenarios

| Scenario | Action | Expected |
|----------|--------|----------|
| Initial state | `useChatMessages()` | `messages=[], isLoading=false` |
| Send message | `sendMessage("Hello")` | appends user msg, sets `isLoading=true` |
| After response | stream ends | `isLoading=false`, assistant msg appended |
| Network error | fetch fails | `isLoading=false`, error message appended |
| Clear | `clearMessages()` | `messages=[]` |
