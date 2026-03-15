# Code Review Plan — Tasks 09–14

270 tests passing, ruff clean. This document highlights the areas most worth human review,
ordered by risk level.

---

## High Priority — Review Carefully

### Task 10: `sp conduct --resume` / `--force` (`src/specsoloist/cli.py`, `manifest.py`)

**Why:** This touches the core build loop and manifest system. The logic for deciding what
to skip vs recompile is subtle — get it wrong and you silently skip specs that should rebuild.

**What to check:**
- `needs_rebuild()` in `manifest.py` — does it correctly detect stale specs? Does it check
  that output files actually exist on disk?
- `_show_resume_plan()` in `cli.py` — is the pre-flight summary accurate?
- `_conduct_with_agent()` — the resume/force context is injected into the conductor agent
  prompt as text instructions. This is best-effort for agent mode; worth understanding the
  limitation.
- `_conduct_with_llm()` — `effective_incremental = not force` is the key line. Verify the
  logic covers all flag combinations (no flags / --resume / --force).
- Mutual exclusion: `--resume` and `--force` use an argparse group — check this is wired
  correctly and gives a clear error if both are passed.

**Tests:** `tests/test_conduct_resume.py` (6 tests), `tests/test_manifest.py` (updated)

---

### Task 11: `env_vars` in Arrangement schema (`schema.py`, `cli.py`, `compiler.py`)

**Why:** Adds a new schema field that affects prompt injection — if the injection logic is
wrong, soloists get misleading environment variable information.

**What to check:**
- `ArrangementEnvVar` model in `schema.py` — fields: `description`, `required`, `example`.
  Verify defaults are sensible (required should probably default to False).
- `compiler.py` — "Environment Variables" section injected into soloist prompts. Check the
  format is clear and only appears when `env_vars` is non-empty.
- `sp doctor --arrangement` in `cli.py` — critical failures for unset required vars,
  informational for optional. Check the output is user-friendly and doesn't crash on missing
  arrangement file.
- `_check_validate_env_vars()` — silently swallows all parse errors (`except Exception: pass`).
  Acceptable for a warning-only path, but worth knowing it's there.
- `examples/nextjs_ai_chat/arrangement.yaml` — `OPENAI_API_KEY` added as example usage.

**Tests:** `tests/test_env_vars.py` (8 tests)

---

### Task 12: Nested session detection (`cli.py`)

**Why:** Environment variable detection for Claude Code / Gemini CLI is inherently fragile —
the env vars used are undocumented and could change. The psutil fallback adds a dependency.

**What to check:**
- `_detect_nested_session()` — which env vars are checked? (`CLAUDECODE`,
  `CLAUDE_CODE_ENTRYPOINT`, `GEMINI_CLI_SESSION`). Are these actually set by current versions?
- psutil fallback — is psutil in the dependencies? Check `pyproject.toml`. If it's optional,
  the code should handle `ImportError` gracefully.
- Warning display — does the "Heads Up" panel give clear enough guidance? The three options
  (separate terminal / --no-agent / Agent tool) should all be actionable.

**Tests:** `tests/test_nested_session.py` (8 tests)

---

## Medium Priority — Spot Check

### Task 09: E2E testing pattern (docs + specs only)

**Why:** No framework code changed — this is docs and new spec files. Lower risk, but worth
checking the Playwright arrangement template is realistic.

**What to check:**
- `docs/e2e-testing.md` — does the guide reflect how `sp conduct` actually works?
- `examples/fasthtml_app/specs/e2e_todos.spec.md` — is the `data-testid` contract clear
  enough for a soloist to implement correctly?
- `examples/fasthtml_app/arrangement.yaml` — were the Playwright additions sensible?
- `examples/fasthtml_app/pyproject.toml` — any new dependencies added here?

---

### Task 14: Database persistence patterns (docs + specs only)

**Why:** No framework code changed — reference specs and docs. The fastlite reference spec
is new and will be injected into soloist prompts for any spec that depends on it.

**What to check:**
- `examples/fasthtml_app/specs/fastlite_interface.spec.md` — does the API documented here
  match the actual fastlite API? Reference specs that drift from reality cause subtle bugs.
- `examples/nextjs_ai_chat/specs/prisma_interface.spec.md` — same question for Prisma v5.
- `docs/database-patterns.md` — is the test fixture pattern (`:memory:` for fastlite,
  `vi.mock` for Prisma) correct and safe?

---

## Lower Priority — Likely Fine

### Task 13: Incremental adoption guide

Pure documentation + an example `original/app.py`. No framework changes.

- Skim `docs/incremental-adoption.md` for accuracy
- Check `examples/fasthtml_incremental/` — does the example app look like a realistic
  starting point for a FastHTML project?

---

## Quick Checks Worth Running

```bash
# Verify the new CLI flags work as documented
uv run sp conduct --help
uv run sp doctor --help
uv run sp init --list-templates

# Spot check env_vars injection
uv run sp validate examples/nextjs_ai_chat/specs/routes.spec.md \
  --arrangement examples/nextjs_ai_chat/arrangement.yaml

# Verify new score specs are valid
uv run sp validate score/arrangement.spec.md
uv run sp validate score/spec_format.spec.md
```

---

## Things the Agent Didn't Do (worth noting)

- **No HK tasks raised** — either the agent found nothing to flag, or it didn't look hard
  enough. Worth keeping an eye out as you review.
- **`sp conduct --resume` in agent mode** is best-effort — the flag is injected as text into
  the conductor prompt, not enforced programmatically. The agent may or may not respect it.
  This is a known limitation worth documenting if it isn't already.
- **psutil** — if task 12 added a psutil dependency, check it's in `pyproject.toml` and
  that the fallback handles the missing-package case gracefully.
