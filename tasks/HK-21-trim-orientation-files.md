# HK-21: Trim dynamic facts from AGENTS.md and ROADMAP.md

**Effort**: Small (< 1 hour)

## Problem

`AGENTS.md` and `ROADMAP.md` embed facts that go stale immediately after every release:
test counts, directory listings, current phase descriptions. These files are trying to be
two incompatible things at once — a timeless orientation guide and a current-state snapshot.

The fix is not to update the numbers. It's to remove them and let authoritative sources
answer: `pytest --collect-only` for test counts, `ls src/specsoloist/` for directory
contents, `tasks/README.md` for current state.

## Changes to `AGENTS.md`

`AGENTS.md` is a symlink to `AGENTS.md` — edit `AGENTS.md` directly.

1. **Key Commands** — remove the test count comment. Change:
   ```
   uv run python -m pytest tests/   # Run tests (270 tests)
   ```
   to:
   ```
   uv run python -m pytest tests/   # Run all tests
   ```

2. **Project Structure** — remove `# pytest tests (270 tests)` comment from the `tests/` line.
   It's noise; the command above already tells agents how to run tests.

3. **Current State section** — replace the entire "Current State (Phase 9: ...)" block with a
   single pointer:
   ```
   ### Current State

   See `tasks/README.md` for active tasks, current phase, and recent completions.
   ```
   The bullet list of phase highlights and the "270 tests passing" line go away entirely.
   `tasks/README.md` is the single source of truth for what's done and what's next.

## Changes to `ROADMAP.md`

1. **Phase 8 description** — remove "270 tests passing." from the end of the paragraph.
   The phase summary describes what was built, not runtime metrics.

2. **Maintenance section** — change:
   ```
   Keep `uv run python -m pytest tests/` green (270 tests)
   ```
   to:
   ```
   Keep `uv run python -m pytest tests/` green
   ```

3. **Phase 9 status** — Phase 9 ("Distribution & Developer Experience") is complete as of
   v0.6.0. Mark it complete and add a brief summary, consistent with the Phase 8 entry style.

4. **Phase 10** — update to reflect the actual current work: `static` artifacts, full project
   reproducibility, and whatever Toby decides is the Phase 10 theme.

## What NOT to change

- The philosophy sections, architecture diagrams, and command references in AGENTS.md — these
  are timeless and should stay.
- The "See Also" links at the bottom of AGENTS.md — these are stable pointers.
- Anything in `tasks/README.md` — that file is allowed to have current-state detail; it's
  designed for it.

## Verification

- `grep -n "270\|355\|402" AGENTS.md` — returns nothing (no test counts)
- `grep -n "270\|355\|402" ROADMAP.md` — returns nothing
- `grep -n "Phase 9" AGENTS.md` — Current State section no longer references Phase 9 by name
- `uv run mkdocs build --strict` — still passes (AGENTS.md is not in the docs nav)
