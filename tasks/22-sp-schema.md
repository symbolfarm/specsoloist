# Task 22: `sp schema [topic]` — Annotated Arrangement Schema

## Why

Agents working on a project that uses SpecSoloist need to discover what fields
`arrangement.yaml` supports without having to read source code. The immediate
manifestation: a real integration missed `output_paths.overrides` and `specs_path`
because nothing surfaced the full schema.

`sp schema` gives agents a fast, accurate, always-in-sync reference derived directly
from the Pydantic models.

## Behaviour

```bash
sp schema                  # Full annotated schema for arrangement.yaml
sp schema output_paths     # Just the output_paths section
sp schema environment      # Just the environment section
sp schema --json           # Machine-readable JSON Schema
```

Output (default, YAML-like annotated format):

```
Arrangement schema  (specsoloist 0.6.0)

target_language: str
  Language for generated code (e.g. "python", "typescript").

specs_path: str  [default: "src/"]
  Directory where spec files (.spec.md) are stored.

output_paths:
  implementation: str  [default: "src/{name}.py"]
    Path template for compiled implementation files. {name} → spec name.
  tests: str  [default: "tests/test_{name}.py"]
    Path template for generated test files.
  overrides:  [default: {}]
    Per-spec path overrides. Key is spec name (without .spec.md).
    data:
      implementation: str  (optional)
        Override implementation path for this spec.
      tests: str  (optional)
        Override tests path for this spec.

environment:
  tools: list[str]  [default: []]
  setup_commands: list[str]  [default: []]
  ...

build_commands:
  test: str   (required)
  lint: str   (optional)
  compile: str  (optional)

model: str  (optional)
  LLM model override. Precedence: --model flag > this field > SPECSOLOIST_LLM_MODEL env.

env_vars:
  <name>:
    description: str  (required)
    required: bool  [default: true]
    example: str  [default: ""]
```

## Implementation

### Source of truth: Pydantic field descriptions

The `Arrangement` and sub-models already have `Field(description=...)` on most fields.
The implementation should walk the Pydantic model's `model_fields` and emit:

- Field name and type
- Default value (if any)
- `description` from the `Field()`

This means the schema output is always in sync with the code — no separate docs to
maintain.

### New function: `schema.py` or `cli.py`

Add a `format_schema(model: type[BaseModel], indent: int = 0) -> str` helper that
recursively renders a Pydantic model as annotated text. Keep it in `cli.py` unless it
grows large enough to warrant its own module.

For `--json`, use `model.model_json_schema()` (Pydantic v2 built-in). No extra code.

### Topic filtering

If a topic is given, check if it matches a top-level field name on `Arrangement`.
If it does, render just that field's sub-model. If not found, print an error listing
valid topics.

```python
valid_topics = list(Arrangement.model_fields.keys())
```

### CLI wiring

Add to `main()`:

```python
schema_parser = subparsers.add_parser(
    "schema",
    help="Show annotated schema for arrangement.yaml"
)
schema_parser.add_argument(
    "topic", nargs="?", default=None,
    help="Field to zoom into (e.g. output_paths, environment)"
)
schema_parser.add_argument(
    "--json", dest="json_output", action="store_true",
    help="Emit JSON Schema instead of annotated text"
)
```

`sp schema` does not need a project context — handle it before the `SpecSoloistCore`
initialisation block (like `init` and `doctor`).

## Files to Read

- `src/specsoloist/schema.py` — all Arrangement models; check which fields already
  have `Field(description=...)` and which need descriptions added
- `src/specsoloist/cli.py` — `main()` structure, where context-free commands are
  handled (around line 252–268)

## Update `score/cli.spec.md`

Add `sp schema` to the CLI spec so the next quine run produces a CLI that includes
this command. Document: the `topic` argument, `--json` flag, and that it requires no
project context.

## Success Criteria

- `sp schema` prints a human-readable annotated schema without error
- `sp schema output_paths` prints only the `output_paths` sub-schema
- `sp schema --json` emits valid JSON Schema (parseable with `json.loads`)
- `sp schema nonexistent` prints a clear error listing valid topics
- Works without an `arrangement.yaml` present (no project context needed)
- All 355 tests pass; `uv run ruff check src/` clean

## Tests

Add `tests/test_cli_schema.py`:
- `sp schema` exits 0 and output contains `"specs_path"` and `"output_paths"`
- `sp schema output_paths` output contains `"overrides"` but not `"specs_path"`
- `sp schema --json` output is valid JSON with `"$schema"` or `"type"` key
- `sp schema bogus` exits non-zero
