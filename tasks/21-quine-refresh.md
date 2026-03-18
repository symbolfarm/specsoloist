# Task 21: Quine Refresh

## Why

The quine was last validated in February 2026 (Phase 6). Since then, Phase 8 and Phase 9
shipped — roughly twenty feature tasks. The score specs describe a codebase that no longer
exists. This matters both as a quality signal ("do our specs actually describe what we
built?") and as a prerequisite for promotion (a broken quine is an embarrassing talking
point if discovered by early users).

Expected state of the score: significantly out of date, not just stale in minor details.
Plan for real archaeology work.

## What changed since the last quine run

Features shipped after the last validated quine that likely require score spec updates:

| Feature | Affected score specs |
|---------|---------------------|
| `type: reference` spec type | `parser.spec.md`, `compiler.spec.md`, `schema.spec.md`, `core.spec.md`, `spec_format.spec.md` |
| Arrangement `dependencies` field | `schema.spec.md` (ArrangementEnvironment), `compiler.spec.md` |
| Arrangement `env_vars` field | `schema.spec.md` (ArrangementEnvVar), `compiler.spec.md`, `cli.spec.md` |
| Arrangement `model` field + `_resolve_model()` | `schema.spec.md`, `core.spec.md` |
| `sp init --template` | `cli.spec.md` |
| `sp conduct --resume` / `--force` | `conductor.spec.md`, `manifest.spec.md`, `cli.spec.md` |
| `sp diff` (spec-drift mode) | new spec needed: `build_diff.spec.md` exists in score/ — check if current |
| `--quiet` / `--json` flags | `cli.spec.md`, `ui.spec.md` (ui.configure()) |
| `sp vibe` | `cli.spec.md`, new `spechestra.spec.md` section or separate spec |
| Pydantic AI provider | `providers/` — new `pydantic_ai_provider.py` replaces gemini/anthropic |
| Nested session detection | `core.spec.md` or `cli.spec.md` (_detect_nested_session) |

Note: `quine_diff.spec.md` exists in score/ — check whether it's current or a draft that
was never completed.

## Files to Read Before Starting

- All specs in `score/` — read every one before touching any of them
- `src/specsoloist/schema.py` — source of truth for Arrangement model fields
- `src/specsoloist/parser.py` — source of truth for spec type handling (reference type)
- `src/specsoloist/compiler.py` — source of truth for what gets injected into prompts
- `src/specsoloist/cli.py` — source of truth for all commands and flags
- `src/specsoloist/core.py` — source of truth for nested session detection, model resolution
- `src/spechestra/composer.py` + `conductor.py` — source of truth for sp vibe, sp compose
- `QUINE_RESULTS.md` — record of the last quine run

## Phase 1: Run and Triage

```bash
sp conduct score/ --model claude-haiku-4-5-20251001 --auto-accept --resume
PYTHONPATH=build/quine/src uv run python -m pytest build/quine/tests/ -q
```

Classify every failure as one of:
- **Wrong**: score spec describes behaviour that was changed — update the spec
- **Missing**: score spec doesn't cover a new feature — add it
- **Broken generation**: soloist produced bad code from a correct spec — re-run without
  `--resume` for that spec, or fix the spec to be clearer

Don't attempt to fix failures mid-triage. Catalogue first, fix second.

## Phase 2: Update Score Specs

Work through the triage list. Keep specs requirements-oriented — describe *what* each
module does, not *how*. When in doubt, read the source and write what a competent
developer would need to know to reimplement it correctly.

For the Pydantic AI provider: the old `providers/gemini.py` and `providers/anthropic.py`
are gone. The score needs a spec (or updated section in `core.spec.md`) describing the
new provider model. Check whether `providers/pydantic_ai_provider.py` needs its own spec
or is an implementation detail covered by `core.spec.md`.

## Phase 3: Full Quine Run

Once triage fixes are in, run without `--resume` to compile everything fresh:

```bash
sp conduct score/ --model claude-haiku-4-5-20251001 --auto-accept
PYTHONPATH=build/quine/src uv run python -m pytest build/quine/tests/ -q
```

Iterate until all tests pass. It's fine to use `--resume` between fix iterations to avoid
recompiling specs that are already correct.

## Success Criteria

- `sp conduct score/ --model claude-haiku-4-5-20251001 --auto-accept` completes without
  errors
- `PYTHONPATH=build/quine/src uv run python -m pytest build/quine/tests/ -q` passes with
  0 failures
- All score specs accurately describe the current `src/` (spot-check: read 3–4 specs
  against their corresponding `src/` files)
- `QUINE_RESULTS.md` updated with the new run results

## Notes

- The quine outputs to `build/quine/` which is gitignored — only the score spec changes
  get committed
- If `quine_diff.spec.md` is stale or speculative, remove it from score/ rather than
  trying to make it work
- The quine CI (`.github/workflows/quine.yaml`) runs weekly with `--resume` — once this
  task is done, trigger it manually to confirm it works end-to-end in CI too
