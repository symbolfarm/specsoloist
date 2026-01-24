# Claude Context for Specular

## What is Specular?

Specular is a "Spec-as-Source" AI coding framework. Users write rigorous Markdown specifications (SRS-style), and Specular uses LLMs to compile them into executable Python code with tests.

**Key insight**: Code is a build artifact. Specs are source of truth.

## Architecture

```
src/specular/
├── core.py          # SpecularCore - thin orchestrator
├── parser.py        # Spec parsing, validation, frontmatter
├── compiler.py      # Prompt construction, LLM code generation
├── runner.py        # Test execution, build file management
├── resolver.py      # Dependency resolution, topological sort
├── manifest.py      # Build caching, incremental builds
├── config.py        # SpecularConfig, env-based loading
├── cli.py           # Human-friendly CLI
├── server.py        # MCP server for AI agents
├── providers/       # LLM backends (Gemini, Anthropic)
└── templates/       # Spec template, global context
```

## Key Commands

```bash
uv run pytest tests/           # Run tests (25 tests)
uv run ruff check src/         # Lint
uv run specular --help         # CLI help
uv run specular-mcp            # Start MCP server
```

## Self-Hosting Spec ("The Quine")

`self_hosting/specular_core.spec.md` is Specular's own specification - it describes itself. Keep this updated when making architectural changes.

## Current State (v0.1.0)

- Phases 1, 1.5, 2a, 2b, 2c complete
- Published to PyPI as `specular-ai`
- CLI and MCP server both functional
- Supports Gemini and Anthropic providers

## What's Next (Phase 3)

See ROADMAP.md. Main items:
- CLI polish (spinners, colors)
- Multi-language support (TypeScript, Go)
- Documentation site
- Better error messages

## Testing Changes

Always run `uv run pytest tests/ && uv run ruff check src/` before committing.
