# Claude Context for SpecSoloist

## What is SpecSoloist?

SpecSoloist is a "Spec-as-Source" AI coding framework. Users write rigorous Markdown specifications (SRS-style), and Specular uses LLMs to compile them into executable Python code with tests.

**Key insight**: Code is a build artifact. Specs are source of truth.

## Key Commands

```bash
uv run pytest tests/           # Run tests (25 tests)
uv run ruff check src/         # Lint
```

## Self-Hosting Spec ("The Quine")

`self_hosting/*` is SpecSoloist's own specification - it describes itself. Keep this updated when making architectural changes.

## What's Next

See ROADMAP.md.

## Testing Changes

Always run `uv run pytest tests/ && uv run ruff check src/` before committing.
