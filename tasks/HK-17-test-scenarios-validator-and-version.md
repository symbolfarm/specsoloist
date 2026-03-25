# HK-17: `yaml:test_scenarios` Validator Fix + `--version` Flag

Two small independent fixes grouped together.

---

## Fix A: Recognise `yaml:test_scenarios` blocks in the validator

### Problem

`_check_spec_quality` in `cli.py` checks for `"## Test Scenarios"` (a Markdown table
section) but does not recognise `` ```yaml:test_scenarios `` blocks. An agent writing
a spec with a well-formed YAML block still receives:

```
⚠ No test scenarios found — soloists compile better with concrete examples
```

The format agents naturally produce when following the spec format is the YAML block:

```yaml:test_scenarios
- description: "basic case"
  inputs: {param: "value"}
  expected_output: "result"
```

### Fix

In `_check_spec_quality` (`cli.py`), update the test scenarios check:

```python
# Before:
if "## Test Scenarios" not in spec_content:
    warnings.append("No test scenarios found — soloists compile better with concrete examples")

# After:
has_scenarios = (
    "## Test Scenarios" in spec_content
    or "```yaml:test_scenarios" in spec_content
)
if not has_scenarios:
    warnings.append(
        "No test scenarios found — soloists compile better with concrete examples.\n"
        "  Add a yaml:test_scenarios block, e.g.:\n"
        "  ```yaml:test_scenarios\n"
        "  - description: \"basic case\"\n"
        "    inputs: {param: \"value\"}\n"
        "    expected_output: \"result\"\n"
        "  ```"
    )
```

Also update the "Fewer than 2 rows" check to skip when the spec uses the YAML block
format instead of a Markdown table (those two checks are coupled — the table row count
check at line ~423 should be guarded by `"## Test Scenarios" in spec_content`, which
it already is, so this may be a no-op).

### Decision: do not accept prose `# Examples`

Free-form prose examples are not machine-readable and don't provide the typed
input/output pairs that soloists need for test generation. A `# Examples` section
should remain unrewarded — the warning should steer authors toward the structured
format, not accept the looser one.

---

## Fix B: `--version` / `-V` flag

### Problem

```
$ sp --version
sp: error: argument command: invalid choice: '--version'
```

Exits with code 2. Standard convention is `--version` prints version and exits 0.

### Fix

Add to the top-level `ArgumentParser` in `main()`, before `subparsers` is created:

```python
import importlib.metadata
_version = importlib.metadata.version("specsoloist")

parser.add_argument(
    "--version", "-V",
    action="version",
    version=f"specsoloist {_version}"
)
```

The `action="version"` built-in prints and exits 0. No other changes needed.

---

## Files to Read

- `src/specsoloist/cli.py` — `_check_spec_quality` (~line 400), `main()` argparse setup
  (~line 28)

## Success Criteria

- `sp validate` on a spec with only a `yaml:test_scenarios` block does **not** warn
  about missing test scenarios
- `sp validate` on a spec with neither a table nor a YAML block shows the improved
  warning message with the example snippet
- `sp --version` prints `specsoloist 0.5.0` (or whatever the current version is)
  and exits 0
- `sp -V` behaves identically
- All 355 tests pass; `uv run ruff check src/` clean

## Tests

Add to the CLI or validator test file:
- Spec with `yaml:test_scenarios` block → no "No test scenarios" warning
- Spec with `## Test Scenarios` table → no warning (existing behaviour preserved)
- Spec with neither → warning includes the example YAML snippet
