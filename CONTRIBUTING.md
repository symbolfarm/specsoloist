# Contributing to SpecSoloist

Guidelines for humans and AI agents contributing to SpecSoloist.

## Required Checks

**All changes must pass these checks before committing:**

```bash
# 1. Run tests (all must pass)
uv run python -m pytest tests/

# 2. Run linting (zero errors required)
uv run ruff check src/
```

If ruff reports errors, fix them or run `uv run ruff check src/ --fix` for auto-fixable issues.

## Files to Keep in Sync

When making changes, ensure these files stay consistent:

| When you change... | Also update... |
|--------------------|----------------|
| CLI commands | `README.md` (CLI Reference table) |
| Architecture/modules | `score/specsoloist.spec.md` |
| Complete a roadmap phase | `ROADMAP.md` |
| Project structure | `AGENTS.md` (Project Structure section) |

## Conventions

### Commit Messages

- Use conventional commit style: `feat:`, `fix:`, `docs:`, `chore:`, `test:`
- Keep the first line under 72 characters
- Reference issues where applicable

### Code Style

- Follow existing patterns in the codebase
- Use type hints for function signatures
- Keep modules focused (single responsibility)

### Specs

- All specs should have the standard sections (Overview, Interface, FRs, NFRs, Design Contract)
- Use `yaml:schema` blocks for interface definitions
- Include test scenarios in a table format

## The Score ("The Quine")

The full SpecSoloist and Spechestra packages should be completely specified and regeneratable from the spec files in `score/`.

**Preferred Workflow: Respec**
Instead of writing specs manually, use `sp respec` to reverse-engineer existing code into a high-fidelity spec:

```bash
uv run sp respec src/specsoloist/some_module.py --out score/some_module.spec.md
```

This invokes an AI agent that analyzes the code, generates the spec, validates it, and fixes any errors.

```
score/
  prompts/             # Agent prompts
  specsoloist.spec.md  # Core package overview
  ui.spec.md           # UI module (bundle)
  config.spec.md       # Config module (bundle)
  ...
```

When you add or modify:
- New modules or classes
- New public methods
- New functional requirements
- New CLI commands

...the score should be updated to reflect these changes.

## See Also

- `AGENTS.md` - Context for AI agents (development and MCP usage)
- `ROADMAP.md` - What to work on next
- `README.md` - User-facing documentation
