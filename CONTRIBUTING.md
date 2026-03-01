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

## Docker & Sandboxing

If you make changes to the Docker environment or `TestRunner`:

1.  **Verify Framework build**: `docker build -t specsoloist -f docker/specsoloist.Dockerfile .`
2.  **Verify Sandbox execution**: 
    - Build sandbox: `docker build -t specsoloist-sandbox -f docker/sandbox.Dockerfile .`
    - Run a test in sandbox: `SPECSOLOIST_SANDBOX=true uv run sp test score/examples/math_utils`

## Files to Keep in Sync

When making changes, ensure these files stay consistent:

| When you change... | Also update... |
|--------------------|----------------|
| CLI commands | `README.md` (CLI Reference table), `docs/reference/cli.md` |
| CLI flags or behaviour | `docs/reference/cli.md` |
| Arrangement system | `docs/guide/arrangement.md` |
| Agent behaviour or subagents | `docs/guide/agents.md`, AND update all three forms: `src/specsoloist/skills/sp-<name>/SKILL.md`, `.claude/agents/<name>.md`, `.gemini/agents/<name>.md` |
| Workflow or iteration loop | `docs/guide/workflow.md` |
| Specs in `score/` | Verify round-trip: regenerate code, run tests |
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

### Specs: Requirements, Not Blueprints

Specs should describe **what**, not **how**:

- **Do**: Public API names, behavior descriptions, edge cases, examples
- **Don't**: Private methods, algorithm names, internal data structures

The quick test: *"Could a competent developer implement this in any language without seeing the original code?"* If the spec prescribes internals, it's a blueprint. If it prescribes requirements, it's genuinely useful.

See `score/spec_format.spec.md` Section 2 for the full philosophy.

## The Score ("The Quine")

The `score/` directory contains SpecSoloist's own specifications. The goal is for `sp conduct score/` to regenerate the entire `src/` directory with passing tests.

**Preferred Workflow: Respec**
Use `sp respec` to extract requirements from existing code into a spec:

```bash
uv run sp respec src/specsoloist/some_module.py --out score/some_module.spec.md
```

This invokes an AI agent that analyzes the code, generates a requirements-oriented spec, validates it, and fixes any errors.

If tests fail after regeneration, use `sp fix`:

```bash
uv run sp fix some_module
```

**Arrangements (Build Configuration)**
Requirements go in `*.spec.md`. Build configuration (output paths, tools, language) belongs in an `Arrangement` file.

**Round-trip Validation**
After respeccing, verify the spec is sufficient by regenerating the code and running tests:

1. Back up the original: `cp src/specsoloist/foo.py src/specsoloist/foo.py.bak`
2. Regenerate from spec (manually or via soloist agent)
3. Run tests: `uv run python -m pytest tests/`
4. If tests pass, the spec captures the requirements correctly

## See Also

- `AGENTS.md` - Context for AI agents (development and MCP usage)
- `ROADMAP.md` - What to work on next
- `README.md` - User-facing documentation
