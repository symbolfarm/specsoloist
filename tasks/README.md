# SpecSoloist — Task Backlog

> **For new Claude sessions:** Read this first. It orients you on project state and points
> you to the right task. Then read `AGENTS.md` for full project context.
> Completed tasks are in `tasks/HISTORY.md`.

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
| Agent-first CLI | Done — `sp conduct`, `sp compose`, `sp respec`, `sp fix`, `sp vibe`, `sp diff` |
| Quine (self-hosting) | Score updated — 22 specs (14 flat + 4 subscribers + 2 spechestra + spec_format + events); last validated 584/584 (2026-03-27); needs re-validation after {path} pattern + new subscriber specs; weekly CI in `.github/workflows/quine.yaml` |
| FastHTML example | Validated — 23 tests passing (`examples/fasthtml_app/`) |
| Next.js example | Validated — 22 tests passing (`examples/nextjs_ai_chat/`) |
| Documentation | Solid — mkdocstrings + Google docstrings live; spec-types.md + example docs complete (HK-11 done) |
| Real-world integration | In progress — definitree (FastHTML/PostgreSQL) uses specsoloist as PyPI dev dependency |

Key commands:
```bash
uv run python -m pytest tests/   # ~545 tests — must stay green
uv run ruff check src/           # must pass with 0 errors
sp conduct score/ --model haiku --auto-accept   # quine attempt (see task 26)
```

---

## Task Status

### Observability & Dashboard (Phase 11)

| # | Task | Effort | Depends | Status |
|---|------|--------|---------|--------|
| 27 | [Event bus and BuildEvent model](27-event-bus.md) | Medium | — | ✅ |
| 28 | [Wire event emission into core/runner/compiler](28-wire-event-emission.md) | Medium | 27 | ✅ |
| 29 | [Provider token tracking](29-provider-token-tracking.md) | Small–Med | 27 | ✅ |
| 30 | [NDJSON subscriber + `--log-file`](30-ndjson-subscriber.md) | Small | 28 | ✅ |
| 31a | [BuildState model + TuiSubscriber](31-tui-dashboard.md) | Small | 28 | ✅ |
| 31b | [Textual app skeleton + spec list](31-tui-dashboard.md) | Medium | 31a | ✅ |
| 31c | [Spec detail panel](31-tui-dashboard.md) | Small–Med | 31b | ✅ |
| 31d | [CLI integration (`--tui`, `sp dashboard`)](31-tui-dashboard.md) | Small | 31b | ✅ |
| 32 | [SSE server (`sp conduct --serve`)](32-sse-server.md) | Medium | 31a | ✅ |

Tasks 27–32 and 35 are done. Next: 33 (task tracking skill) or 34 (NDJSON replay).

### Other Features

| # | Task | Effort | Depends | Status |
|---|------|--------|---------|--------|
| 33 | [Formalize task tracking as agent skill](33-task-format-skill.md) | Medium | — | 🔲 |
| 34 | [`sp dashboard --replay`](34-ndjson-replay.md) | Small | 31b | 🔲 |
| 35 | [Directory-based spec discovery (`{path}` pattern)](35-directory-based-spec-discovery.md) | Medium | — | ✅ |
| 36 | [External dependency declaration (`requires:` in frontmatter)](36-external-dependency-declaration.md) | Medium | — | 🔲 |
| 37 | [`sp diff` defaults to all-specs + daily CI drift check](37-diff-all-default.md) | Small | — | ✅ |
| 38 | [TUI startup feedback](38-tui-startup-feedback.md) | Small | 31d | ✅ |
| 39 | [TUI file viewer (spec, code, tests)](39-tui-file-viewer.md) | Small–Med | 31c | 🔲 |

### 🔲 Housekeeping

| # | Task | Status |
|---|------|--------|
| HK-27 | [README refresh — badges, logo, demo GIF, fix PyPI links](HK-27-readme-refresh.md) | 🔲 |

See also: [spechestra-tasks.md](spechestra-tasks.md) for the Spechestra (web dashboard) backlog.

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

When done with a task, move it to `tasks/HISTORY.md` and commit.

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
spawning. Run from a terminal outside Claude Code, or use `--no-agent`. Alternatively, use
the `Agent` tool with `subagent_type="conductor"` from within a Claude Code session.

**Subprocess `cwd=` must use `Path(__file__).parent.parent`.** Never pass a literal string
like `cwd="."` — it breaks when tests are run from any directory other than the repo root.
Use `Path(__file__).parent.parent` to resolve the repo root relative to the test file, or
define a module-level `REPO_ROOT = Path(__file__).parent.parent` constant and reference it.

---

## Key Architectural Decisions (already made)

- **`type: reference`** — use for any spec documenting a third-party library. No implementation
  generated. Spec body injected into prompts of dependent soloists via `reference_specs: dict[str, ParsedSpec]`
  passed through `compile_code()`. Verification snippets compiled to a test file.

- **Multi-spec web apps** — separate layout, routing, and state into distinct specs. One
  combined spec can't express UI completeness. See `tasks/HISTORY.md` task 06 for the pattern.

- **Arrangements are build config** — language, output paths, tool versions, env var names.
  Specs are language-agnostic. Never put language-specific details in specs.
