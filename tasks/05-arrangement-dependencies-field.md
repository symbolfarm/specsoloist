# Task: Add `dependencies` Field to Arrangement Schema

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.
The arrangement system is documented in `score/arrangement.spec.md` and implemented in
`src/specsoloist/schema.py` (the `Arrangement` Pydantic model).

Web apps depend on versioned libraries that can have breaking API changes between releases.
Currently there is no machine-readable way to record which library versions an arrangement
was written and verified against. Version constraints appear only as comments:

```yaml
# Requires: pip install python-fasthtml>=0.12
constraints:
  - Use python-fasthtml (import from fasthtml.common)
```

This means:
- Soloists have no structured version context to put in generated imports or docs
- `setup_commands` like `uv add python-fasthtml` don't pin versions
- When a library upgrades and breaks generated code, there's no record of what version worked
- `sp doctor` or `sp validate` can't warn about missing or outdated dependencies

## What to Build

### 1. Schema change (`src/specsoloist/schema.py`)

Add an optional `dependencies` field to the `ArrangementEnvironment` model:

```python
class ArrangementEnvironment(BaseModel):
    tools: list[str] = []
    setup_commands: list[str] = []
    dependencies: dict[str, str] = {}   # package_name -> version_spec
```

Example arrangement usage:
```yaml
environment:
  tools: [uv, pytest]
  setup_commands: [uv sync]
  dependencies:
    python-fasthtml: ">=0.12,<0.13"
    starlette: ">=0.52"
    pytest: ">=7.0"
```

For TypeScript/Node projects:
```yaml
environment:
  tools: [node, npm]
  setup_commands: [npm install]
  dependencies:
    ai: "^3.0.0"
    "@ai-sdk/openai": "^0.0.20"
    vitest: "^1.0.0"
```

The value is a version specifier string in the native package manager format (PEP 440 for
Python, semver range for npm). No parsing required — store as string, pass to soloists verbatim.

### 2. Compiler injection (`src/specsoloist/compiler.py`)

When building the prompt for a soloist, include the arrangement's `dependencies` dict in the
context block. Format it clearly:

```
## Dependency Versions

This project uses the following versioned dependencies. Use APIs compatible with these versions:

  python-fasthtml  >=0.12,<0.13
  starlette        >=0.52
  pytest           >=7.0
```

If `dependencies` is empty, omit the section entirely (no noise).

### 3. Arrangement validation (`src/specsoloist/schema.py` or `cli.py`)

When `sp validate` runs on a spec that has an arrangement, and the arrangement has
`dependencies`, check that `setup_commands` includes a command that would install them
(e.g. contains `uv sync`, `uv add`, `npm install`, or `pip install`). If not, warn:
"⚠ dependencies declared but no install command found in setup_commands".

This is a warning, not an error.

### 4. Update the FastHTML example arrangement

Update `examples/fasthtml_app/arrangement.yaml` to use the new field:

```yaml
environment:
  tools: [uv, pytest]
  setup_commands: [uv sync]
  dependencies:
    python-fasthtml: ">=0.12,<0.13"
    starlette: ">=0.52"
    httpx: ">=0.24"
    pytest: ">=7.0"
```

### 5. Update `score/arrangement.spec.md`

Document the new `dependencies` field with its purpose, format, and an example for both
Python (uv/pip) and Node (npm) projects.

## Files to Read First

- `src/specsoloist/schema.py` — `Arrangement`, `ArrangementEnvironment` models
- `src/specsoloist/compiler.py` — `build_prompt()`, how arrangement context is injected
- `score/arrangement.spec.md` — arrangement spec to update
- `examples/fasthtml_app/arrangement.yaml` — to update
- `tests/test_arrangement.py` — existing arrangement tests to extend

## Success Criteria

1. `Arrangement.environment.dependencies` is parsed from YAML and accessible as a dict.
2. A soloist prompt for a spec in a project with `dependencies` includes the version table.
3. A project with `dependencies` but no install command in `setup_commands` produces a warning
   from `sp validate`.
4. `examples/fasthtml_app/arrangement.yaml` uses the new field.
5. `score/arrangement.spec.md` documents the new field.
6. All existing tests pass: `uv run python -m pytest tests/`
7. Ruff passes: `uv run ruff check src/`
8. New tests in `tests/test_arrangement.py` cover: parsing `dependencies`, empty `dependencies`,
   missing install command warning.
