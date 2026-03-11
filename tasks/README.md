# SpecSoloist — Task Backlog

> **For new Claude sessions:** Read this first. It orients you on project state and points
> you to the right task. Then read `AGENTS.md` for full project context.

---

## What Is SpecSoloist?

A spec-driven AI coding framework. Developers write `.spec.md` files describing *what* code
should do; the `sp conduct` command spawns AI agents that write the implementation and tests.

The broader goal right now: **make SpecSoloist ready for developing and maintaining FastHTML
and Next.js web applications.**

---

## Current State

| Layer | Status |
|-------|--------|
| Core framework | Stable — parser, compiler, runner, resolver, manifest |
| Agent-first CLI | Done — `sp conduct`, `sp compose`, `sp respec`, `sp fix` |
| Quine (self-hosting) | Validated — `sp conduct score/` regenerates `src/` with 563 tests passing |
| FastHTML example | Validated — 23 tests passing (`examples/fasthtml_app/`) |
| Next.js example | Not yet run — `examples/nextjs_ai_chat/` exists but unvalidated |
| Web-dev readiness | In progress — tasks 04–14 cover the remaining gaps |

Key commands:
```bash
uv run python -m pytest tests/   # 52 tests — must stay green
uv run ruff check src/           # must pass with 0 errors
sp conduct score/ --model haiku --auto-accept   # quine attempt
```

---

## Task Status

### ✅ Done

| # | Task | Summary |
|---|------|---------|
| 01 | Fix `--auto-accept` scoping | `bypassPermissions` now scoped to quine runs only |
| 02 | Implement `sp test --all` | Runs tests for every compiled spec, shows summary table |
| 03 | Validate FastHTML example | `examples/fasthtml_app/` — 23 tests passing, README written |
| 04 | `reference` spec type | Parser validation, compiler injection, no code gen, verification tests, `sp validate`/`sp status` display |
| HK-01 | Consolidate IMPROVEMENTS + ROADMAP | Trimmed §0 done-items from IMPROVEMENTS.md; fixed §0g (`_compile_single_spec` reference spec guard) and §0h (dep key normalised to `"from"` in core.py) |
| 05 | Arrangement `dependencies` field | `ArrangementEnvironment.dependencies: dict[str, str]`; injected as "Dependency Versions" table in soloist prompts; `sp validate --arrangement` warns if no install command; FastHTML arrangement and score spec updated |

### 🔲 Decisions

| File | Topic | Status |
|------|-------|--------|
| `decisions/01-sp-perform.md` | Keep / fix / remove `sp perform` | **Decided: Option A — remove** |

### 🔲 Housekeeping

| # | Task | Effort | Summary |
|---|------|--------|---------|
| **HK-02** | Small fixes | Tiny | Fix `Optional[ArrangementEnvironment]` type hint; add comment on reference spec early return; move dependency warning to `_resolve_arrangement()` |
| **HK-03** | Remove `sp perform` | Small | Remove `cmd_perform`, `SpecConductor.perform/build_and_perform/_execute_step`, `PerformResult`, `StepResult`. See `decisions/01-sp-perform.md` for full removal checklist. |

### 🔲 To Do — in priority order

| # | Task | Effort | Depends on | Summary |
|---|------|--------|------------|---------|
| ~~**04**~~ | ~~`reference` spec type~~ | ~~Medium~~ | ~~—~~ | ~~Done~~ |
| ~~**05**~~ | ~~Arrangement `dependencies` field~~ | ~~Small~~ | ~~—~~ | ~~Done~~ |
| **06** | FastHTML app refactor | Small–Medium | 04, 05 | Split `app.spec.md` into layout/routes/state; add delete button; migrate `fasthtml_interface` to `type: reference` |
| **07** | Validate Next.js AI chat | Medium | 04 | Write `vercel_ai_interface` as `reference` spec; run `sp conduct`; get tests passing |
| **08** | Arrangement templates | Small | 06, 07 | `sp init --template python-fasthtml/nextjs-vitest/nextjs-playwright` |
| **09** | E2E testing pattern | Medium | 08 | Playwright arrangement, `data-testid` spec contract, FastHTML E2E example |
| **10** | `sp conduct --resume` | Medium | — | Skip already-compiled specs; cascade recompile on dep change |
| **11** | Arrangement `env_vars` field | Small | 05 | Declared env var names; `sp doctor` warns if unset |
| **12** | Nested session warning | Small | — | Detect when running inside Claude Code; print friendly message |
| **13** | Incremental adoption guide | Small–Medium | 06 | `sp respec` workflow for existing FastHTML/Next.js projects |
| **14** | Database persistence patterns | Medium | 04, 06 | `fastlite` + Prisma reference specs; test fixture patterns |

---

## How to Pick Up a Task

1. **Read this file** (done ✓)
2. **Read `AGENTS.md`** — project structure, key commands, current phase
3. **Pick the lowest-numbered uncompleted task** (or one the user specifies)
4. **Read the task file** in full — context, steps, files to read, success criteria
5. **Read all source files listed in the task** before writing any code or forming an approach.
   Task files intentionally leave some implementation decisions open; the right answer usually
   emerges from reading the code. Decide, then proceed — don't ask about decisions the source
   files resolve.
6. **Verify** with `uv run python -m pytest tests/` and `uv run ruff check src/` before committing

When done with a task, mark it ✅ in this file and commit.

---

## Working Principles

These apply to every task. Knowing them upfront prevents the most common mistakes:

**Minimal footprint.** Extend existing call sites rather than restructuring them. If `compile_code()`
needs a new parameter, add it with a default of `None` so all existing callers still work.

**Display logic lives in `cli.py`.** The validator, parser, and compiler return data. `cli.py`
formats it for humans. Don't embed display strings in lower layers.

**Unit tests for framework changes; end-to-end as a smoke test.** When a task changes parser,
compiler, or runner behaviour, write unit tests for those layers directly. End-to-end via
`sp conduct` is a sanity check, not the primary verification.

**Reference specs have three sections** — `# Overview` (required), `# API` (required),
`# Verification` (recommended — warn if absent). The `# Verification` section contains
3–10 lines of import and smoke-test snippets compiled into `tests/test_{name}.py`. This makes
reference specs *verified documentation* that fails CI when the library API drifts.

**No generated files committed.** `src/` and `tests/` in examples are gitignored. Only specs,
arrangements, READMEs, and framework source committed.

**`sp conduct` nested session.** Running `sp conduct` inside Claude Code blocks subprocess
spawning. Run from a terminal outside Claude Code, or use `--no-agent`.

---

## Key Architectural Decisions (already made)

- **`type: reference`** — use for any spec documenting a third-party library. No implementation
  generated. Spec body injected into prompts of dependent soloists via `reference_specs: dict[str, ParsedSpec]`
  passed through `compile_code()`. Verification snippets compiled to a test file.

- **Multi-spec web apps** — separate layout, routing, and state into distinct specs. One
  combined spec can't express UI completeness. See task 06 for the pattern.

- **Arrangements are build config** — language, output paths, tool versions, env var names.
  Specs are language-agnostic. Never put language-specific details in specs.
