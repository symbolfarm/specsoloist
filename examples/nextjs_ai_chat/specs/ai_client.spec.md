---
name: ai_client
type: bundle
status: draft
dependencies: []
---

# AI Client

Adapter wrapping the [Vercel AI SDK](https://sdk.vercel.ai) (`ai` package). The rest of the
project depends on this module, not on the SDK directly — swapping providers only requires
changing this file.

## `streamChat(messages, options?)`

Streams a chat completion using `streamText()` from the `ai` package.

**Parameters:**
- `messages: Message[]` — conversation history. Each `Message` has:
  - `role: "user" | "assistant" | "system"`
  - `content: string`
- `options?: { model?: string; maxTokens?: number }` — optional overrides.
  - `model` defaults to `"gpt-4o-mini"`.
  - `maxTokens` defaults to `1024`.

**Returns:** `Promise<ReadableStream<string>>` — a text stream suitable for passing to
the Next.js `StreamingTextResponse` helper.

**Throws:** Re-throws any error from the underlying SDK with an additional `cause` property
set to the original error.

## `listModels()`

Returns the list of model IDs available through this adapter.

**Returns:** `string[]` — e.g. `["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]`.

## Types

```typescript
export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatOptions {
  model?: string;
  maxTokens?: number;
}
```

## Test Scenarios

| Scenario | Input | Expected |
|----------|-------|----------|
| Stream response | `streamChat([{role:"user", content:"Hi"}])` | Returns a `ReadableStream` |
| Custom model | `streamChat(msgs, {model:"gpt-4o"})` | Uses gpt-4o |
| List models | `listModels()` | Array of strings, non-empty |
