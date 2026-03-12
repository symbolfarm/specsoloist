# HK-04: Conductor Should Write `config_files` Before `setup_commands`

## Problem

The `arrangement.yaml` `environment.config_files` field declares files that should be
written before the build starts (typically `package.json`, `tsconfig.json`, etc.).
The `environment.setup_commands` field declares commands to run after those files exist
(typically `npm install`).

Currently, the conductor **does not write `config_files`** before running `setup_commands`.
This means `npm install` fails on a fresh clone because there is no `package.json` yet.
The user has to create `package.json` manually — which defeats the purpose of having it
in the arrangement.

Surfaced during task 07 (`examples/nextjs_ai_chat/`): had to create `package.json`
by hand before `npm install` would run.

## Expected Behaviour

When a conductor (or `sp conduct`) loads an arrangement, the full lifecycle should be:

```
1. Write config_files from arrangement   ← currently missing
2. Run setup_commands
3. Compile specs in dependency order
4. Run tests
```

The `config_files` field is a `dict[str, str]` mapping filename → content (already fully
defined in `arrangement.yaml`). Writing these files is trivial; the gap is that it isn't
wired up.

## Where to Look

- `src/spechestra/conductor.py` — where setup_commands are run; add config_files write here
- `src/specsoloist/schema.py` — `ArrangementEnvironment.config_files` field definition
- `tests/test_arrangement.py` — add a test that config_files are written before setup_commands

The conductor agent (`.claude/agents/conductor.md`) also mentions setup_commands but not
config_files — update the agent prompt if the conductor is expected to handle this directly.

## Success Criteria

1. `sp conduct examples/nextjs_ai_chat/specs/ --arrangement arrangement.yaml` on a clean
   directory (no `package.json`) writes `package.json` and `tsconfig.json` before running
   `npm install`.
2. Test in `tests/test_arrangement.py` verifies config_files are written to disk.
3. All existing tests pass: `uv run python -m pytest tests/`
4. Ruff passes: `uv run ruff check src/`
