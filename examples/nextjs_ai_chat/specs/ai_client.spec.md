---
name: ai_client
type: bundle
status: draft
dependencies:
  - vercel_ai_interface
---

# Overview

Adapter wrapping the [Vercel AI SDK](https://sdk.vercel.ai) (`ai` package, v3.x). The rest
of the project depends on this module, not on the SDK directly — swapping providers only
requires changing this file.

The `Message` and `ChatOptions` types are exported for use by callers.

# Functions

```yaml:functions
streamChat:
  inputs:
    messages: "Message[] — conversation history, each with role and content"
    options: "ChatOptions? — optional overrides (model, maxTokens)"
  outputs:
    stream: "Promise<ReadableStream<string>> — text stream for StreamingTextResponse"
  behavior: "Streams a chat completion via streamText() from the ai package. Uses result.toAIStream() to get a ReadableStream. Defaults: model='gpt-4o-mini', maxTokens=1024. Re-throws SDK errors with .cause set to the original error."

listModels:
  inputs: {}
  outputs:
    models: "string[] — available model IDs"
  behavior: "Returns the list of model IDs supported by this adapter, e.g. ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo']."
```

# Types

## Message

```typescript
export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}
```

## ChatOptions

```typescript
export interface ChatOptions {
  model?: string;      // defaults to "gpt-4o-mini"
  maxTokens?: number;  // defaults to 1024
}
```

# Examples

| Scenario | Input | Expected |
|----------|-------|----------|
| Stream response | `streamChat([{role:"user", content:"Hi"}])` | Resolves to a `ReadableStream` |
| Custom model | `streamChat(msgs, {model:"gpt-4o"})` | Uses gpt-4o |
| List models | `listModels()` | Non-empty array of strings |
| SDK error | SDK throws | Re-throws with `.cause` set |
