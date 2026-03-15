# Code Review Plan — Phase 9 (Tasks 15–20)

355 tests passing, ruff clean. 12 commits on main. This document highlights the areas most
worth human review, ordered by risk level.

---

## High Priority — Review Carefully

### Task 20: Pydantic AI provider (`src/specsoloist/providers/pydantic_ai_provider.py`, `cli.py`, `pyproject.toml`)

**Why:** Largest diff (1241 lines including `uv.lock`). New external dependency (`pydantic-ai-slim`)
added to the project. Backward-compat claim needs verification — existing `gemini` and `anthropic`
providers must be unaffected.

**What to check:**
- `pyproject.toml` — `pydantic-ai-slim` added as a hard dependency (not optional). This means
  it's installed for all users, even those only using Gemini or Anthropic. Is that intentional?
- `pydantic_ai_provider.py` — does `PydanticAIProvider` implement the same interface as
  `GeminiProvider` / `AnthropicProvider`? Check `generate()` signature and return type.
- Provider routing in `cli.py` / `config.py` — new provider names are `openai`, `openrouter`,
  `ollama`, `google`. How does `google` relate to the existing `gemini` provider? Are both
  supported or is one deprecated?
- `sp doctor` output — does it show API key status cleanly for all 5 providers? Does it crash
  if a provider's package isn't importable?
- `uv.lock` — 807-line diff. Worth a quick scan to confirm no unexpected transitive dependencies
  were pulled in.

**Tests:** `tests/test_pydantic_ai_provider.py` (27 tests — check if any make real API calls)

---

### Task 15: `sp diff` (`src/specsoloist/spec_diff.py`, `cli.py`)

**Why:** Entirely new 500-line module doing AST analysis. Complex logic for symbol extraction
and test gap detection. First new core feature since Phase 7.

**What to check:**
- `spec_diff.py` — how does it extract "declared public symbols" from a spec? Parsing markdown
  headers / code blocks is fragile; check what happens with unusual spec formats.
- AST symbol extraction from Python — does it handle all the patterns soloists generate
  (classes, functions, `__all__`, re-exports)? Does it handle non-Python outputs gracefully?
- `TEST_GAP` detection — how does it match spec scenarios to test functions? Name-based
  heuristic? Could produce false positives/negatives.
- `build_diff.py` — this file appeared alongside `spec_diff.py`. What is it? Is it used by
  any command, or leftover scaffolding?
- `--json` output — does `sp diff --json` produce a stable, documented schema?
- CLI integration in `cli.py` — `sp diff <name>` (single arg) vs `sp diff <file1> <file2>`
  (two-arg file diff from before). Are the two modes clearly separated and do they conflict?

**Tests:** `tests/test_spec_diff.py` (22 tests)

---

### Task 19: `sp vibe` (`src/specsoloist/cli.py`)

**Why:** Orchestrates the entire compose→conduct pipeline in one command. Lots of edge cases
around `--resume`, `--pause-for-review`, and failure modes mid-pipeline.

**What to check:**
- What happens if `sp compose` fails partway through? Does `sp vibe` surface the error cleanly
  or silently proceed to `sp conduct` with incomplete specs?
- `--pause-for-review` — how is this implemented? Does it actually block until the user
  continues, or does it just print a message?
- `--resume` (addendum mode) — what does "addendum mode" mean here vs `sp conduct --resume`?
  Are they the same flag passed through, or does vibe do something different?
- Brief input — accepts a `.md` file or a plain string. What's the fallback if the string
  looks like a filepath that doesn't exist?
- Does `sp vibe` work with `--no-agent`? The test suite probably only tests the `--no-agent`
  path — check that agent-mode wiring is present too.

**Tests:** `tests/test_vibe.py` (11 tests)

---

## Medium Priority — Spot Check

### Task 16: `--quiet` / `--json` flags (`src/specsoloist/cli.py`, `ui.py`)

**Why:** Global flags that affect all commands. `ui.configure()` reinitialises the Rich
console — if called at the wrong time or twice, could cause subtle display bugs.

**What to check:**
- `ui.configure(quiet=True)` — when is this called relative to other `ui.*` calls? If any
  output happens before `configure()` runs, it won't be suppressed.
- `--quiet` should suppress all non-error output. Verify it doesn't also swallow errors.
- `--json` is per-subcommand (`status`, `compile`, `validate`). Is the JSON schema consistent
  across commands (same envelope structure)?
- Does `sp conduct --quiet` actually suppress soloist output, or only the conductor's own
  output? (Soloist output likely goes through a subprocess or agent, so may not be suppressed.)

**Tests:** `tests/test_quiet_json_flags.py` (13 tests)

---

### Task 17: Model pinning (`schema.py`, `cli.py`, `conductor.py`, `score/arrangement.spec.md`)

**Why:** Precedence chain (`--model` > `arrangement.model` > env var > default) is easy to
get subtly wrong. Conductor receives a `model` parameter that must forward correctly.

**What to check:**
- `_resolve_model()` in `cli.py` — verify precedence order against the task spec. Does it
  handle `None` at each level correctly (no `None` leaking into provider calls)?
- `conductor.build()` — was the model parameter actually wired through, or just accepted and
  ignored?
- `score/arrangement.spec.md` — was the new `model` field added here? The score should match
  the implementation.

**Tests:** `tests/test_model_pinning.py` (12 tests)

---

## Lower Priority — Likely Fine

### Task 18: Quine CI (`.github/workflows/quine.yaml`)

Pure YAML, no framework changes. Fast to review.

- Check the schedule: `cron: '0 2 * * 0'` — is Sunday 2am UTC correct and intentional?
- `--auto-accept` flag is used — confirm this doesn't require an interactive TTY in CI.
- Artifact upload: `build/quine/` with 30-day retention — sensible.
- Does the workflow need any secrets configured in the repo settings (e.g. `ANTHROPIC_API_KEY`)?
  If so, is this documented?

---

### HK-07 / HK-08: Quine naming fix + docs review

- Check if `score/` specs now reference `composer.py` / `conductor.py` (not `speccomposer` /
  `specconductor`).
- Skim updated docs in `docs/` for any obvious drift or broken links.

---

## Quick Checks Worth Running

```bash
# Smoke test new commands
uv run sp diff --help
uv run sp vibe --help
uv run sp --quiet status
uv run sp --json status

# Verify provider routing
uv run sp doctor

# Check the mystery file
cat src/specsoloist/build_diff.py

# Confirm no real API calls in new tests
grep -r "ANTHROPIC_API_KEY\|GEMINI_API_KEY\|openai.api_key" tests/test_pydantic_ai_provider.py tests/test_vibe.py

# Full test suite
uv run python -m pytest tests/ -q
uv run ruff check src/
```

---

## Things Worth Flagging

- **`build_diff.py`** — appeared alongside `spec_diff.py` but isn't mentioned in the commit
  message. Unclear if it's intentional, used, or leftover scaffolding. Check before keeping.
- **`pydantic-ai-slim` as hard dependency** — adds install weight for all users. Consider
  whether it should be optional (`pydantic-ai-slim` extras in `pyproject.toml`).
- **Worktree isolation didn't work** — the ralph agent committed directly to `main` because
  the prompt explicitly specified the main repo working directory. All 12 commits are on `main`
  with no branch to review. For next time: omit `Working directory:` from the prompt when
  using `isolation: "worktree"`.
