# HK-05: Bundle Spec Documentation Gap (`yaml:functions` required, docs show prose)

## Problem

The bundle spec format requires a `` ```yaml:functions `` block for the parser to
recognise functions — but the documentation shows prose-style `## functionName` headings.

**What the parser expects:**
```markdown
# Functions

```yaml:functions
my_function:
  inputs: {x: integer}
  outputs: {result: integer}
  behavior: "Does something"
```
```

**What the docs show** (`spec_format.spec.md` §6.1 and the bundle template example):
```markdown
# Functions

## compute_file_hash(path) -> string

SHA-256 hash of a file...
```

This mismatch caused `examples/nextjs_ai_chat/specs/ai_client.spec.md` to fail
`sp validate` with "Bundle must have at least one function or type defined" — because
it was written in the documented prose style, not the YAML-block style the parser needs.

## Affected Files

- `score/spec_format.spec.md` §6.1 — the bundle example uses prose headings
- The bundle template in `src/specsoloist/parser.py:_generate_bundle_template()` is
  *correct* (uses `yaml:functions`), so that's fine
- Any existing specs written in prose style will silently have no parsed functions

## Fix Options

**Option A (preferred): Update `spec_format.spec.md` §6.1** to match the actual parser.
Replace the prose-style function headings in the bundle example with the correct
`yaml:functions` block format. Keep the `manifest` bundle example but make it accurate.

**Option B: Make the parser accept both formats** — parse both `yaml:functions` blocks
*and* `## functionName` prose headings as function definitions. This is more work and
would need clear spec about which takes precedence.

Option A is simpler and keeps one canonical format. Option B is more forgiving for spec
authors but adds parser complexity.

## Success Criteria

1. `score/spec_format.spec.md` §6.1 bundle example uses `yaml:functions` blocks.
2. A new user writing a bundle spec by following the docs produces a spec that passes
   `sp validate` without modification.
3. All existing tests pass: `uv run python -m pytest tests/`
