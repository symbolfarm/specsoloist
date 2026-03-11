# Task: Add Vercel AI Reference Spec and Validate the Next.js AI Chat Example

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.

The `examples/nextjs_ai_chat/` directory contains a Next.js App Router + Vercel AI SDK chat app:
- `specs/ai_client.spec.md` — adapter wrapping the Vercel AI SDK (`ai` package)
- `specs/chat_ui.spec.md` — route handler + React hook (depends on `ai_client`)
- `arrangement.yaml` — build config (TypeScript, npm, vitest)

**This example has never been run.** There is also a gap: the Vercel AI SDK (`ai` package) is
new enough that LLMs may hallucinate its API, just as they do with FastHTML. This task creates
a `reference` spec for the Vercel AI SDK (see task 04 for the `reference` type) and then
validates the full example end-to-end.

**Prerequisite:** Task 04 (`reference` spec type) must be complete before this task, as
`vercel_ai_interface` should use `type: reference`.

This task has two parts:

1. **Write `vercel_ai_interface.spec.md`** — a `reference` spec documenting the Vercel AI SDK subset used
2. **Validate the full example end-to-end** — run `sp conduct`, get tests passing, write a README

## Part 1: Write `vercel_ai_interface.spec.md`

Create `examples/nextjs_ai_chat/specs/vercel_ai_interface.spec.md`.

This should be a `reference` spec (type: reference) — no `yaml:functions`, no schema block,
just clear `# Overview` and `# API` sections describing the subset of the `ai` package
(`npm install ai`) that `ai_client.spec.md` uses. No code will be generated from it;
it exists to ground soloists in the correct API.

### What to document

Research the Vercel AI SDK v3/v4 API. The key surface area used by this project:

**From `ai` (core package):**
- `streamText({ model, messages, maxTokens? })` — streams a text response. Returns a
  `StreamTextResult` with a `.textStream` property that is an `AsyncIterable<string>`.
- `StreamingTextResponse(stream, init?)` — a Next.js `Response` subclass that streams text.
  Pass `.textStream` to it.
- `Message` type: `{ role: "user" | "assistant" | "system"; content: string }`

**From `@ai-sdk/openai`:**
- `openai(modelId: string)` — creates an OpenAI model instance. Pass to `streamText`'s
  `model` field.
- Requires `OPENAI_API_KEY` environment variable.

**Version note:** The arrangement uses `"ai": "^3.0.0"`. Verify that the API above matches
v3 (not v4, which has breaking changes). The `StreamingTextResponse` helper was deprecated
in v4 in favour of `result.toDataStreamResponse()`. Document whichever version the
arrangement pins.

### Spec format

```markdown
---
name: vercel_ai_interface
type: reference
status: stable
---

# Overview

The subset of the [`ai`](https://sdk.vercel.ai) package (v3.x, `npm install ai`) used in
this project. Specs that call the Vercel AI SDK should list `vercel_ai_interface` as a
dependency. No code is generated from this spec — it exists to give soloists accurate API
documentation. Verify API against v3 (not v4, which has breaking changes).

# API

## `streamText(options)`

...

## `StreamingTextResponse`

...

## Types

...
```

### Update `ai_client.spec.md`

Add `vercel_ai_interface` to the `dependencies` field in the frontmatter so the conductor
compiles it first.

## Part 2: Validate the Example End-to-End

### 1. Install dependencies

```bash
cd examples/nextjs_ai_chat
npm install
```

### 2. Validate specs

```bash
sp validate vercel_ai_interface
sp validate ai_client
sp validate chat_ui
```

Fix any structural errors. Quality hints (⚠) are acceptable.

### 3. Run `sp conduct`

```bash
sp conduct specs/ --arrangement arrangement.yaml --auto-accept
```

Dependency order: `vercel_ai_interface` → `ai_client` → `chat_ui`

Expected output locations (per arrangement, including overrides):
- `src/vercel_ai_interface.ts` (may be minimal — just type re-exports)
- `src/ai_client.ts`
- `src/app/api/chat/route.ts` (override for `chat_route`)
- `src/hooks/useChatMessages.ts` (override for `use_chat_messages`)
- `tests/vercel_ai_interface.test.ts`
- `tests/ai_client.test.ts`
- `tests/chat_route.test.ts`
- `tests/useChatMessages.test.ts`

**Output paths:** `chat_route` and `use_chat_messages` use per-spec output path overrides
already configured in `arrangement.yaml`. The conductor will read these and tell each
soloist exactly where to write its output file — no manual path resolution needed.

### 4. Run tests

```bash
npx vitest run
```

### 5. Fix any issues

If tests fail, investigate whether the issue is in the spec, the arrangement, or the
interface spec. Do NOT manually edit generated code — fix specs and re-compile.

Common failure modes for this stack:
- **Vitest can't import `ai` or `@ai-sdk/openai`** — the npm package names or versions
  in `arrangement.yaml`'s `package.json` may be wrong. Check and fix.
- **`streamText` API mismatch** — the generated code calls the wrong API. Improve
  `vercel_ai_interface.spec.md` and recompile `ai_client`.
- **React hook tests fail** — `useChatMessages` uses `fetch` which isn't available in
  vitest's Node environment. The spec or test should use `vi.mock('cross-fetch')` or
  configure vitest with a jsdom environment.
- **TypeScript strict mode errors** — the tsconfig uses strict mode. If generated code
  has implicit `any`, the compile step (`npx tsc --noEmit`) will fail.

### 6. Write a README

Once tests pass, write `examples/nextjs_ai_chat/README.md` documenting:
- What the example demonstrates
- Prerequisites (Node 18+, npm, `OPENAI_API_KEY`)
- How to run `sp conduct`
- How to run the tests
- How to start the dev server (`npm run dev`)
- The output path mismatch (if unresolved) and what manual steps are needed
- Any Vercel AI SDK API quirks discovered during validation

## Files to Read First

- `examples/nextjs_ai_chat/specs/ai_client.spec.md`
- `examples/nextjs_ai_chat/specs/chat_ui.spec.md`
- `examples/nextjs_ai_chat/arrangement.yaml`
- `examples/fasthtml_app/specs/fasthtml_interface.spec.md` — use as a model for the interface spec format
- `AGENTS.md`

## Success Criteria

1. `examples/nextjs_ai_chat/specs/vercel_ai_interface.spec.md` exists and passes `sp validate`.
2. `ai_client.spec.md` lists `vercel_ai_interface` as a dependency.
3. `npx vitest run` in `examples/nextjs_ai_chat/` passes with 0 failures.
4. `examples/nextjs_ai_chat/README.md` exists and documents all the points above.
5. Any changes to specs or arrangement are committed; generated `src/`/`tests/` files are gitignored.
6. Generated `src/` and `tests/` files are gitignored (not committed).
