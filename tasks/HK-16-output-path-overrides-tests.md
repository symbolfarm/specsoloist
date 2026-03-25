# HK-16: Verify and Test `output_paths.overrides`

## Background

`ArrangementOutputPathOverride` and `overrides: Dict[str, ArrangementOutputPathOverride]`
already exist in `schema.py`. The YAML structure required to use overrides is:

```yaml
output_paths:
  implementation: tree_lm/{name}.py
  tests: tests/test_{name}.py
  overrides:
    data:
      implementation: tree_lm/data/postgres/data.py
    components:
      implementation: tree_lm/html/components.py
```

Each override is an object with optional `implementation` and/or `tests` keys.
Omitting a key falls back to the template. This is more expressive than a flat
`{name: path}` dict.

There are currently no targeted tests for this code path, and it is not documented
in the arrangement templates or score spec.

## What to Do

### 1. Write unit tests

Add tests to `tests/test_schema.py` (or `tests/test_arrangement.py`):

```python
def test_output_paths_overrides_impl_only():
    """Override implementation path; tests path falls back to template."""
    raw = {
        "implementation": "src/{name}.py",
        "tests": "tests/test_{name}.py",
        "overrides": {
            "data": {"implementation": "tree_lm/data/postgres/data.py"}
        }
    }
    paths = ArrangementOutputPaths(**raw)
    assert paths.resolve_implementation("data") == "tree_lm/data/postgres/data.py"
    assert paths.resolve_tests("data") == "tests/test_data.py"  # falls back to template

def test_output_paths_overrides_both():
    """Override both implementation and tests paths."""
    ...

def test_output_paths_no_override():
    """No override → template is applied."""
    ...

def test_output_paths_overrides_yaml_roundtrip():
    """Full Arrangement with overrides section serialises/deserialises via PyYAML."""
    import yaml
    raw_yaml = """
target_language: python
specs_path: specs/
output_paths:
  implementation: "tree_lm/{name}.py"
  tests: "tests/test_{name}.py"
  overrides:
    data:
      implementation: tree_lm/data/postgres/data.py
    components:
      implementation: tree_lm/html/components.py
build_commands:
  test: "uv run python -m pytest tests/ -q"
"""
    data = yaml.safe_load(raw_yaml)
    arr = Arrangement(**data)
    assert arr.output_paths.resolve_implementation("data") == "tree_lm/data/postgres/data.py"
    assert arr.output_paths.resolve_implementation("model") == "tree_lm/model.py"
```

### 2. Update `score/arrangement.spec.md`

Document the `overrides` sub-field under `output_paths`. Show the nested YAML syntax.
Clarify that each key is a spec name (without `.spec.md`) and each value has optional
`implementation` and/or `tests` sub-keys.

### 3. Verify `resolve_implementation` uses `.format(name=name)` not `.replace()`

Check `schema.py` line ~102. The current implementation uses:
```python
return self.implementation.format(name=name)
```
This is correct for `{name}` templates. Confirm it handles both `{name}` and legacy
`{name}` syntax. If `.replace("{name}", name)` is used instead, either is fine but
note it in the task completion.

## Files to Read

- `src/specsoloist/schema.py` — `ArrangementOutputPaths`, `ArrangementOutputPathOverride`,
  `resolve_implementation`, `resolve_tests`
- `tests/test_schema.py` — existing test patterns for schema models
- `score/arrangement.spec.md` — where to add documentation

## Success Criteria

- At least 4 new tests covering: impl-only override, both-override, no-override fallback,
  YAML round-trip with `Arrangement`
- All tests pass: `uv run python -m pytest tests/ -q`
- `score/arrangement.spec.md` documents the overrides syntax with a YAML example
- `uv run ruff check src/` clean
