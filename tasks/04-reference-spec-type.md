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

## What to Build

### 1. Parser changes (`src/specsoloist/parser.py`)

Add `"reference"` to the set of valid spec types. A reference spec requires:
- `# Overview` section (what the library is, import path, version pinned)
- `# API` section (functions, types, gotchas — prose or tables, no `yaml:functions` required)

No `yaml:schema`, no `yaml:functions`, no `yaml:steps`. Validate and return gracefully.

In `_validate_reference_sections(parsed)`:
- Error if `# Overview` is missing
- Error if `# API` is missing (soloists need something substantive to read)
- Warn if no version is mentioned in Overview (hint: "Pin the version the API was verified against")

In `parse_spec()`, handle `spec_type == "reference"` like `"function"/"type"` but extract
nothing — no schema, no functions, no steps. Just parse metadata and body.

### 2. Compiler changes (`src/specsoloist/compiler.py`)

The conductor and soloists need to treat reference specs differently:

**No code generation for reference specs.** When a spec has `type: reference`, the compiler
should produce no implementation file and no test file. The build step is a no-op.

**Inject as context for dependents.** When building a prompt for spec B that lists a reference
spec A as a dependency, include the full body of A's spec file in the prompt under a clear
heading like `## Reference: fasthtml_interface`. This is the primary value: soloists reading
spec B see the API contract inline.

Concretely, `build_prompt(spec, dependencies)` should distinguish between:
- Normal dependencies: inject their public interface summary (type signatures, function names)
- Reference dependencies: inject their full spec body verbatim

### 3. Runner changes (`src/specsoloist/runner.py`)

When `run_tests(name)` is called for a reference spec, return a synthetic pass result
immediately without executing anything. No test file should exist or be expected.

### 4. `sp validate` output

`sp validate` should display reference specs differently — no warning about missing schema or
test scenarios, since those don't apply. Display the type as `reference (context only)` in
the output so users understand no code will be generated.

### 5. Update spec format documentation

Update `score/spec_format.spec.md`:
- Add `reference` to the spec types table with purpose "Third-party API documentation — no
  code generated; injected as context for dependent specs"
- Add a section `6.6 Reference Spec` with a worked example (use FastHTML as the example)
- Update the Section Reference table (§8) with required sections for reference type

### 6. Update the `fasthtml_interface` spec

Once the type is implemented, update
`examples/fasthtml_app/specs/fasthtml_interface.spec.md` to use `type: reference` instead of
`type: bundle`. Remove the `yaml:functions` block (it's no longer needed or appropriate) and
ensure the `# API` section contains the full human-readable API documentation.

### 7. Update `.claude/agents/soloist.md` and `.gemini/agents/soloist.md`

Add a note that soloists should treat reference specs in their dependency list as API
documentation to read and follow, not as modules to import or re-implement.

## Files to Read First

- `src/specsoloist/parser.py` — especially `parse_spec()`, `_validate_*_sections()`, `ParsedSpec`
- `src/specsoloist/compiler.py` — `build_prompt()`, dependency injection
- `src/specsoloist/runner.py` — `run_tests()`
- `score/spec_format.spec.md` — current spec type definitions
- `examples/fasthtml_app/specs/fasthtml_interface.spec.md` — the first spec to migrate
- `.claude/agents/soloist.md`
- `AGENTS.md`

## Success Criteria

1. `sp validate examples/fasthtml_app/specs/fasthtml_interface.spec.md` passes with
   `type: reference` and no `yaml:functions` block.
2. `sp conduct examples/fasthtml_app/specs/ --arrangement examples/fasthtml_app/arrangement.yaml`
   does not attempt to generate `src/fasthtml_interface.py` or `tests/test_fasthtml_interface.py`.
3. The generated `src/app.py` (which depends on `fasthtml_interface`) correctly uses the
   FastHTML API — demonstrating that reference injection worked.
4. `uv run pytest examples/fasthtml_app/tests/ -v` passes (only `test_app.py` exists now).
5. `sp validate` on a reference spec shows no spurious warnings about missing schema or examples.
6. All existing tests pass: `uv run python -m pytest tests/`
7. Ruff passes: `uv run ruff check src/`
8. `score/spec_format.spec.md` documents the reference type with a worked example.

## Notes

The `yaml:functions` block in the current `fasthtml_interface.spec.md` was a workaround —
it's semantically wrong. Once `reference` exists, delete it entirely. The `# API` section
(prose + tables) is what soloists actually read; structured YAML added nothing.

Consider: should reference specs appear in `sp status` output? Probably yes, as `CONTEXT`
rather than `COMPILED`, so users can see they exist and are being used.
