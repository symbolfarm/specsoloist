# Next.js AI Chat (TypeScript)

`examples/nextjs_ai_chat/` is a Next.js App Router + Vercel AI SDK streaming chat
application, built entirely from specs. It is one of SpecSoloist's two primary validated
examples.

## What it demonstrates

- **`type: reference` for TypeScript**: `vercel_ai_interface` documents the Vercel AI
  SDK v3 API — preventing LLM hallucinations when generating code that calls the SDK
- **Adapter pattern**: `ai_client` wraps the AI SDK so other modules never import it
  directly, making the rest of the system testable without a real AI key
- **Output path overrides**: `arrangement.yaml` maps specs to non-standard file
  locations (`src/app/api/chat/route.ts`, `src/hooks/useChatMessages.ts`) — the right
  way to handle Next.js App Router conventions
- **Vitest**: all tests use [Vitest](https://vitest.dev) rather than Jest

## Spec structure

| Spec | Type | Output |
|------|------|--------|
| `vercel_ai_interface` | `reference` | _(none — API docs only)_ |
| `ai_client` | `bundle` | `src/ai_client.ts` |
| `chat_route` | `bundle` | `src/app/api/chat/route.ts` |
| `use_chat_messages` | `bundle` | `src/hooks/useChatMessages.ts` |

Dependency order: `vercel_ai_interface` → `ai_client` → `chat_route` + `use_chat_messages`
(the last two are independent and compile in parallel).

## Running it

```bash
cd examples/nextjs_ai_chat
npm install --no-package-lock
sp conduct specs/ --arrangement arrangement.yaml --auto-accept
npx vitest run
```

Expected: **22 tests passed** across 4 test files.

To run the app itself, set `OPENAI_API_KEY` and then `npm run dev`.

## Output path overrides

Next.js App Router requires files in specific directory locations that don't match
SpecSoloist's default flat output. The arrangement maps each spec to the right path:

```yaml
specs:
  chat_route:
    output_path: src/app/api/chat/route.ts
  use_chat_messages:
    output_path: src/hooks/useChatMessages.ts
```

This is the standard pattern for any framework with opinionated file placement.
See [Arrangement](../guide/arrangement.md) for the full `output_path` reference.
