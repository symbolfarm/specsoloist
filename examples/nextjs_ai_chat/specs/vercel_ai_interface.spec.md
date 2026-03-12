---
name: vercel_ai_interface
type: reference
status: stable
---

# Overview

The subset of the [`ai`](https://sdk.vercel.ai) package (v3.x, `npm install ai`) and
`@ai-sdk/openai` (v0.0.x) used in this project. Specs that call the Vercel AI SDK should
list `vercel_ai_interface` as a dependency. No code is generated from this spec — it
exists to give soloists accurate API documentation.

**Version note:** This documents v3 of the `ai` package. v4 has breaking changes:
`StreamingTextResponse` was deprecated in v4 in favour of `result.toDataStreamResponse()`.
The arrangement pins `"ai": "^3.0.0"` and `"@ai-sdk/openai": "^0.0.1"` — use the v3 API.

**Package imports:**
```typescript
import { streamText, StreamingTextResponse } from 'ai';
import type { Message } from 'ai';
import { openai } from '@ai-sdk/openai';
```

# API

## `streamText(options)`

Streams a text generation response from a language model.

```typescript
import { streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

const result = await streamText({
  model: openai('gpt-4o-mini'),
  messages: [{ role: 'user', content: 'Hello' }],
  maxTokens: 1024,
});
```

**Options:**
- `model` — a model instance created by a provider factory (e.g. `openai('gpt-4o-mini')`)
- `messages: Message[]` — conversation history
- `maxTokens?: number` — maximum tokens to generate
- `system?: string` — system prompt (alternative to including a system message in `messages`)

**Returns:** `StreamTextResult` — an object with:
- `.textStream: AsyncIterable<string>` — async iterable of text chunks
- `.toAIStream(): ReadableStream` — converts to a `ReadableStream` compatible with
  `StreamingTextResponse`. **Use this method** when building a streaming HTTP response.

## `StreamingTextResponse`

A Next.js `Response` subclass that streams text to the client. Pass the result of
`result.toAIStream()` as the first argument.

```typescript
import { StreamingTextResponse, streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

export async function POST(req: Request) {
  const { messages } = await req.json();
  const result = await streamText({
    model: openai('gpt-4o-mini'),
    messages,
  });
  return new StreamingTextResponse(result.toAIStream());
}
```

**Signature:** `new StreamingTextResponse(stream: ReadableStream, init?: ResponseInit)`

- `stream` — a `ReadableStream` (use `result.toAIStream()`)
- `init?` — optional `ResponseInit` for additional headers/status

Sets `Content-Type: text/plain; charset=utf-8` and `Transfer-Encoding: chunked` automatically.

## `openai(modelId)` from `@ai-sdk/openai`

Creates an OpenAI model instance for use with `streamText`.

```typescript
import { openai } from '@ai-sdk/openai';

const model = openai('gpt-4o-mini');  // uses OPENAI_API_KEY env var
```

**Parameter:** `modelId: string` — e.g. `"gpt-4o-mini"`, `"gpt-4o"`, `"gpt-4-turbo"`

**Environment:** Requires `OPENAI_API_KEY` to be set. Throws if the key is missing at
request time (not at import time).

## Types

```typescript
// From the 'ai' package
export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}
```

## Testing with Vitest

The `ai` package uses ESM. Configure vitest to handle it:

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
  },
});
```

Mock `streamText` and the OpenAI provider in tests — never make real API calls:

```typescript
import { vi } from 'vitest';

vi.mock('ai', () => ({
  streamText: vi.fn(),
  StreamingTextResponse: class StreamingTextResponse extends Response {
    constructor(stream: ReadableStream) { super(stream); }
  },
}));

vi.mock('@ai-sdk/openai', () => ({
  openai: vi.fn(() => ({})),
}));
```

# Verification

```typescript
// Verify the package exports exist at the correct paths
import { streamText, StreamingTextResponse } from 'ai';
import { openai } from '@ai-sdk/openai';
import type { Message } from 'ai';

// Type check: Message shape
const msg: Message = { role: 'user', content: 'hello' };
console.assert(msg.role === 'user');
console.assert(typeof streamText === 'function');
console.assert(typeof openai === 'function');
```
