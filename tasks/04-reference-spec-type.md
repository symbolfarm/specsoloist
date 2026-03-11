# Task: Add `reference` Spec Type for Third-Party API Documentation

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.

When using SpecSoloist with external libraries — especially new or version-sensitive ones like
FastHTML or the Vercel AI SDK — soloists need accurate API documentation. Today there is no
clean spec type for this purpose:

- `type: bundle` is the closest but requires a `yaml:functions` block that implies "implement
  these functions". Soloists may misread this as an implementation target rather than a reference.
- `type: type` requires a schema block and implies a data structure.

Both are semantic mismatches. A reference spec is **documentation only** — the library supplies
the implementation. No code should be generated for it. It exists purely to ground soloists.

See `IMPROVEMENTS.md §4e` for the original proposal. The naming discussion concluded on
`reference` (not `interface`, which collides with programming language interfaces, and not
`context`, which is too vague).

## Reference Spec Structure

A reference spec has three sections:

| Section | Required | Purpose |
|---------|----------|---------|
| `# Overview` | Yes | Library name, PyPI/npm package, version range, import path |
| `# API` | Yes | Documented functions, types, HTMX attributes, gotchas — prose or tables |
| `# Verification` | Recommended (warn if absent) | Minimal test snippets run against the real installed library |

The `# Verification` section is what makes a reference spec *verified documentation* rather
than just documentation. It contains 3–10 lines of import and smoke tests that fail if the
library version changes incompatibly:

```markdown
# Verification

```python
from fasthtml.common import fast_app, serve, Div, Form, Input, Button
app, rt = fast_app()
assert callable(rt)
div = Div("hello", id="x")
assert "hello" in str(div)
```
```

The runner compiles these snippets into `tests/test_{name}.py`. If `# Verification` is absent,
no test file is generated (no error — just no verification).

## What to Build

### 1. Parser changes (`src/specsoloist/parser.py`)

Add `"reference"` to the set of valid spec types. In `_validate_reference_sections(parsed)`:
- **Error** if `# Overview` is missing
- **Error** if `# API` is missing
- **Warn** if `# Verification` is absent ("No verification snippets — spec cannot detect library version drift")
- **Warn** if no version range is mentioned in `# Overview`
- Suppress all other quality warnings that don't apply to reference specs (missing schema,
  missing test scenarios, short description)

In `parse_spec()`, handle `spec_type == "reference"`: extract nothing from the body (no schema,
no functions, no steps) — just parse metadata and body. Add a helper `_extract_verification_snippet(body) -> str`
that pulls the code block from `# Verification` if present.

### 2. Compiler changes (`src/specsoloist/compiler.py`)

**Architectural note:** To inject reference spec bodies into dependent prompts, `compile_code()`
needs access to the parsed dependency specs — not just the current spec's dependency list.
Add `reference_specs: dict[str, ParsedSpec] | None = None` to `compile_code()`,
`compile_tests()`, and `_build_import_context()`. In `core.py`'s `compile_spec()`, after
parsing the current spec, parse each dependency to check its type, and collect reference ones:

```python
reference_specs = {}
for dep in (spec.metadata.dependencies or []):
    dep_name = dep if isinstance(dep, str) else dep.get("name", "")
    try:
        dep_spec = self.parser.parse_spec(dep_name)
        if dep_spec.metadata.type == "reference":
            reference_specs[dep_name] = dep_spec
    except Exception:
        pass  # missing dep handled elsewhere
```

Pass `reference_specs` to `compiler.compile_code(spec, ..., reference_specs=reference_specs)`.

In `_build_import_context()`: for deps in `reference_specs`, emit the full spec body under
`## Reference: {name}` instead of the normal `- Import from '{name}'` line. Regular deps
keep existing behaviour. Mixed dep lists (some reference, some normal) work correctly.

**No implementation generated for reference specs.** In `core.py`'s `compile_spec()`, detect
`spec.metadata.type == "reference"` and skip code compilation entirely. Return early with a
message like `"Reference spec — no code generated"`.

### 3. Runner changes (`src/specsoloist/runner.py`)

**Verification tests:** When `compile_tests()` is called for a reference spec that has a
`# Verification` section, generate a minimal test file from the snippet. The generated file
should contain exactly one test function that runs the snippet (wrapped in `def test_verify():`)
plus the necessary imports.

**If `# Verification` is absent:** `compile_tests()` for a reference spec returns an empty
string / no-op. No test file is written.

**`run_tests(name)` for reference spec with no verification:** Return a synthetic pass result
immediately without executing anything.

### 4. `sp validate` output

In `cli.py`, after calling the validator: if `parsed.metadata.type == "reference"`, display:
```
✔ fasthtml_interface.spec.md is VALID
  type: reference — context only, no implementation will be generated
```
The string `"reference — context only..."` is display logic in `cli.py`, not in the validator.

### 5. `sp status` output

In `cmd_status()`, check `parsed.metadata.type == "reference"` before the manifest lookup.
If reference type, show `[blue]CONTEXT[/]` in the Compiled column and `[dim]—[/]` in the
Tests column instead of looking up the manifest. This prevents the misleading `✗ never` row.

### 4. `sp validate` output

`sp validate` should display reference specs differently — no warning about missing schema or
test scenarios, since those don't apply. Display the type as `reference (context only)` in
the output so users understand no code will be generated.

### 6. Update spec format documentation

Update `score/spec_format.spec.md`:
- Add `reference` to the spec types table
- Add section `6.6 Reference Spec` with structure table (Overview/API/Verification), the
  `# Verification` pattern, and the fastHTML spec as a worked example
- Update the Section Reference table (§8) with required/recommended sections for reference type

### 7. Update the `fasthtml_interface` spec

Migrate `examples/fasthtml_app/specs/fasthtml_interface.spec.md` to `type: reference`.
Remove the `yaml:functions` block. Ensure `# Overview`, `# API`, and `# Verification` are
all present. The `# Verification` section should include enough smoke tests to detect a
breaking FastHTML API change (import check + `fast_app()` call + one component render).

### 8. Update `.claude/agents/soloist.md` and `.gemini/agents/soloist.md`

Add a note that reference specs in a dependency list are API documentation to read and
follow accurately — not modules to import from, and not things to re-implement.

## Files to Read First

- `src/specsoloist/parser.py` — `parse_spec()`, `_validate_*_sections()`, `ParsedSpec`
- `src/specsoloist/compiler.py` — `compile_code()`, `_build_import_context()` — read these
  carefully before deciding the injection approach; the right answer follows from the call sites
- `src/specsoloist/core.py` — `compile_spec()` — this is where `reference_specs` dict is built
- `src/specsoloist/runner.py` — `run_tests()`
- `src/specsoloist/cli.py` — `cmd_status()`, `sp validate` output formatting
- `score/spec_format.spec.md` — current spec type definitions
- `examples/fasthtml_app/specs/fasthtml_interface.spec.md` — spec to migrate
- `.claude/agents/soloist.md`
- `AGENTS.md`

## Success Criteria

1. `sp validate examples/fasthtml_app/specs/fasthtml_interface.spec.md` passes, showing
   `type: reference — context only` and no spurious schema/test-scenario warnings.
2. `sp validate` on a reference spec missing `# Verification` shows a warning (not an error).
3. `sp conduct examples/fasthtml_app/specs/` does not generate `src/fasthtml_interface.py`.
4. The generated `src/app.py` correctly uses the FastHTML API, confirming injection worked.
5. `tests/test_fasthtml_interface.py` IS generated from `# Verification` snippets and passes
   against the installed `python-fasthtml` package.
6. `sp status` shows reference specs as `CONTEXT` rather than `✗`.
7. All existing tests pass: `uv run python -m pytest tests/`
8. Ruff passes: `uv run ruff check src/`
9. New unit tests cover:
   - Parser: valid reference spec; missing `# API` is an error; missing `# Verification` is a warning
   - Compiler: `_build_import_context` injects full body for reference deps, import lines for normal deps
   - Runner: reference spec with `# Verification` generates a test file; without it, no test file
   - Runner: `run_tests()` on a reference spec with no verification returns synthetic pass

## Notes

**Why `# Verification` matters:** A reference spec without verification is documentation that
can silently drift. If `python-fasthtml` renames `fast_app()`, the spec still says `fast_app()`
and soloists generate broken code with full confidence. The verification test catches this
immediately. This is especially important for FastHTML, fastlite, and Vercel AI SDK — all
fast-moving, pre-1.0 libraries. For stable libraries (React, Python stdlib) verification is
less critical, hence it's a warning rather than an error.

**Architectural decision recorded:** Inject reference spec bodies via `reference_specs: dict[str, ParsedSpec]`
passed through `compile_code()` and `_build_import_context()`, built in `core.py`'s `compile_spec()`.
This was chosen over passing raw content strings because ParsedSpec.body is already available
and the type check (is this dep a reference?) must happen somewhere anyway.
