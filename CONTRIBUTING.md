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
| Architecture/modules | `self_hosting/specular_core.spec.md` |
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

## The Self-Hosting Spec ("The Quine")

The full SpecSoloist and Spechestra packages should be completely specificied and regeneratable from the spec files in `self_hosting`.

**Preferred Workflow: "Lift & Shift"**
Instead of writing specs manually, use the `sp lift` command to reverse-engineer the existing code into a high-fidelity spec.

```bash
uv run sp lift src/specsoloist/some_module.py --test tests/test_some_module.py
```

This ensures the spec accurately reflects the implementation (Behavior, Contracts, Examples).

```
self_hosting/
  specsoloist.spec.md  # Core package overview
  ...
```

When you add or modify:
- New modules or classes
- New public methods
- New functional requirements
- New CLI commands

...the self-hosting spec should be updated to reflect these changes. This is "the quine" - the project's specification of itself.

## See Also

- `AGENTS.md` - Context for AI agents (development and MCP usage)
- `ROADMAP.md` - What to work on next
- `README.md` - User-facing documentation
