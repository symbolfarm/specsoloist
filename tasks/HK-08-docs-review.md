# HK-08: Review and Update docs/ Content

## Problem

The `docs/` directory contains several guides that may have drifted from the current
implementation. New features added in Phase 8 (env_vars, nested session, --resume,
arrangement templates, etc.) may not be reflected.

## Files to Review

```
docs/
  guide/
    workflow.md       — main workflow guide; check sp vibe mention, compose→conduct flow
    arrangement.md    — check env_vars field, dependencies field, model pinning (task 17)
    agents.md         — check nested session warning, current phase state
  reference/
    cli.md            — must match current sp --help output exactly
  database-patterns.md  — new in Phase 8; likely accurate
  e2e-testing.md        — new in Phase 8; likely accurate
  incremental-adoption.md — new in Phase 8; likely accurate
```

## Steps

1. Read each file in `docs/guide/` and `docs/reference/`
2. Compare against actual CLI (`sp --help`, `sp conduct --help`, etc.) and source
3. Update any stale content
4. Add missing features:
   - `env_vars` field in arrangement guide
   - `--resume` / `--force` flags in workflow/conduct docs
   - Arrangement templates in arrangement guide
   - Nested session warning in agents guide
5. Run `uv run python -m pytest tests/ -q` and `uv run ruff check src/` (docs-only changes
   should not affect tests, but verify nothing was accidentally touched)

## Auto-Generated Docs Question

The user asked whether docs can be auto-generated from docstrings. Options:

- **MkDocs + mkdocstrings**: Already using MkDocs Material. `mkdocstrings[python]` plugin
  auto-generates API reference pages from docstrings. Add to `docs/reference/api.md`
  with `::: specsoloist.cli` directives.
- **pdoc**: Simpler, generates standalone HTML from docstrings. Less integrated.

However: most of SpecSoloist's user-facing docs are *conceptual* guides (workflow, arrangement,
agents), not API reference. The CLI is the interface, not the Python API. Auto-generated
docs would complement, not replace, the hand-written guides.

**Recommendation:** Add `mkdocstrings` to the dev dependencies and generate an API reference
page for the core modules (`core`, `schema`, `parser`). This is low effort and useful for
contributors, but not the primary doc improvement.

This can be done as part of this task or as a separate small task.

## Success Criteria

- All files in `docs/guide/` accurately describe current behaviour
- `docs/reference/cli.md` matches current `sp --help` output
- No references to removed features (`sp perform`, old type names, 52-test count)
- Optionally: `mkdocstrings` added and `docs/reference/api.md` generated
