# Next.js AI Chat — SpecSoloist Example

A Next.js App Router + Vercel AI SDK streaming chat application, built entirely from specs.

## What This Demonstrates

- A `type: reference` spec (`vercel_ai_interface`) that documents the Vercel AI SDK v3 API,
  preventing LLM hallucinations when generating code that uses the SDK
- An adapter pattern (`ai_client`) that wraps the AI SDK so other modules never import it directly
- A Next.js App Router route handler (`chat_route`) for the `/api/chat` streaming endpoint
- A React hook (`use_chat_messages`) managing chat state and streaming responses
- Output path overrides in `arrangement.yaml` for non-standard file locations

## Prerequisites

- Node.js 18+
- npm
- `OPENAI_API_KEY` environment variable (for running the app; not required for tests)

## Running `sp conduct`

From the SpecSoloist repository root:

```bash
cd examples/nextjs_ai_chat
npm install --no-package-lock
sp conduct specs/ --arrangement arrangement.yaml --auto-accept
```

Or using `uv run` from the repo root:

```bash
uv run sp conduct examples/nextjs_ai_chat/specs/ \
  --arrangement examples/nextjs_ai_chat/arrangement.yaml \
  --auto-accept
```

Dependency order: `vercel_ai_interface` → `ai_client` → `chat_route` + `use_chat_messages`

### Output paths

| Spec | Implementation | Tests |
|------|---------------|-------|
| `vercel_ai_interface` | _(none — reference spec)_ | `tests/vercel_ai_interface.test.ts` |
| `ai_client` | `src/ai_client.ts` | `tests/ai_client.test.ts` |
| `chat_route` | `src/app/api/chat/route.ts` | `tests/chat_route.test.ts` |
| `use_chat_messages` | `src/hooks/useChatMessages.ts` | `tests/useChatMessages.test.ts` |

The `chat_route` and `use_chat_messages` specs use per-spec output path overrides in
`arrangement.yaml` so their files land in the correct Next.js directory structure.

## Running the Tests

```bash
cd examples/nextjs_ai_chat
npm install --no-package-lock   # if not already done
npx vitest run
```

Expected output: **22 tests passed, 0 failures** across 4 test files.

## Starting the Dev Server

```bash
export OPENAI_API_KEY=sk-...
npm run dev
```

Open `http://localhost:3000`. The chat UI will be available once you add a page component
(see below).

## Notes

### `@ai-sdk/openai` version

The arrangement pins `@ai-sdk/openai: "^0.0.9"`. Version `0.0.1` was published without a
`dist/` directory and cannot be imported. Use `0.0.9` or later.

### Vercel AI SDK v3 vs v4

This example uses `ai@^3.0.0`. In v4, `StreamingTextResponse` was replaced by
`result.toDataStreamResponse()`. The `vercel_ai_interface.spec.md` documents the v3 API.
If you upgrade to v4, update the reference spec and recompile `ai_client`.

### React hook testing

The `use_chat_messages` tests exercise the hook's state logic directly rather than using
`@testing-library/react`, since that package is not in devDependencies. The hook module
is verified by import, and the streaming/state logic is tested via a controller that mirrors
the hook implementation. For full render-cycle testing, add `@testing-library/react`.

### Missing page component

`sp conduct` generates only what is specified. To run the app end-to-end you will need
to add `src/app/page.tsx` with a chat UI component that calls the `useChatMessages` hook
and renders the message list.
