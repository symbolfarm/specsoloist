# HK-12: Fix pytest TestResult/TestRunner collection warnings in quine

## Why

The quine's generated `test_runner.py` triggers two `PytestCollectionWarning` messages because
pytest tries to collect `TestResult` and `TestRunner` as test classes (they start with `Test`).
These are harmless but untidy — they appear in every quine test run and in CI output.

```
PytestCollectionWarning: cannot collect test class 'TestResult' because it has a __init__ constructor
PytestCollectionWarning: cannot collect test class 'TestRunner' because it has a __init__ constructor
```

The root cause is that `runner.spec.md` doesn't tell soloists to avoid the collision, so the
generated tests import `TestResult`/`TestRunner` at module scope where pytest sees them.

## Fix

Add a constraint to `score/runner.spec.md`:

```markdown
# Constraints
- ...existing constraints...
- Test files must not import `TestResult` or `TestRunner` at module scope in a way that
  pytest can collect them. Import inside test functions, or alias on import
  (e.g. `from runner import TestRunner as Runner`).
```

## Steps

1. Edit `score/runner.spec.md` — add the above constraint to the `# Behavior` or end of file.
2. Re-run just the runner spec in the quine (use `--resume` to skip the rest):
   ```bash
   sp conduct score/runner.spec.md --model claude-haiku-4-5-20251001 --auto-accept
   PYTHONPATH=build/quine/src uv run python -m pytest build/quine/tests/test_runner.py -v
   ```
3. Confirm no `PytestCollectionWarning` in the output.

## Success Criteria

- `PYTHONPATH=build/quine/src uv run python -m pytest build/quine/tests/ -q` shows 0 warnings
