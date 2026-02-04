# SpecSoloist for AI Agents

This file provides context for AI agents working with SpecSoloist, whether developing the framework itself or using it as a tool.

> **Note**: `CLAUDE.md` and `GEMINI.md` are symlinks to this file. This ensures all AI agents receive the same context regardless of which file their tooling reads.

## What is SpecSoloist?

SpecSoloist is a "Spec-as-Source" AI coding framework. Users write rigorous Markdown specifications (SRS-style), and SpecSoloist uses LLMs to compile them into executable Python code with tests.

**Key insight**: Code is a build artifact. Specs are the source of truth.

Now with **Spechestra** features: define and run multi-agent orchestration workflows directly from specs.

---

## For Agents Developing SpecSoloist

### Key Commands

```bash
uv run python -m pytest tests/   # Run tests (30 tests)
uv run ruff check src/           # Lint (must pass with 0 errors)
```

### Project Structure

```
src/specsoloist/       # Core package - individual spec compilation
  core.py              # SpecSoloistCore orchestrator
  parser.py            # Spec parsing and validation
  compiler.py          # LLM prompt construction
  runner.py            # Test execution
  resolver.py          # Dependency graph
  config.py            # Configuration
  cli.py               # CLI (sp command)
  schema.py            # Interface validation (Pydantic models)
  providers/           # LLM backends (Gemini, Anthropic)
src/spechestra/        # Orchestration package - high-level workflows
  composer.py          # SpecComposer: Plain English → specs
  conductor.py         # SpecConductor: Parallel builds + perform
tests/                 # pytest tests
self_hosting/          # The Quine - SpecSoloist's own spec
  examples/            # Example specs in new format
```

### Self-Hosting Spec ("The Quine")

`self_hosting/specular_core.spec.md` is SpecSoloist's own specification - it describes itself. Keep this updated when making architectural changes.

### Before Committing

See `CONTRIBUTING.md` for required checks and conventions.

---

## For Agents Using SpecSoloist (MCP)

SpecSoloist is **Agent-Native**. It provides high-level tools via the Model Context Protocol (MCP) that allow an AI agent to act as a Software Architect.

### The Role of the Agent

When using SpecSoloist, the agent's role shifts from "Writing Code" to **"Defining Behavior"**:

- **The Agent (Architect)**: Writes `*.spec.md` files
- **SpecSoloist (Builder)**: Compiles specs to code, writes tests, runs them, fixes bugs

### MCP Toolset

| Tool | Description |
|------|-------------|
| `create_spec(name, description, type)` | Create a new component specification |
| `compile_spec(name)` | Compile the spec into source code |
| `compile_tests(name)` | Generate a test suite from the spec |
| `run_tests(name)` | Execute tests and return results |
| `attempt_fix(name)` | Self-healing loop: analyze failures and patch code/tests |

### Example System Prompt

> You are a Lead Software Architect. Your goal is to build robust software using the **SpecSoloist Framework**.
>
> **Rules:**
> 1. **Never write source code** (Python/JS) directly. Always create or edit `*.spec.md` files.
> 2. **Be Rigorous**: When editing specs, clearly define **Functional Requirements (FRs)** and **Design Contracts**.
> 3. **Iterate**:
>    - Create Spec -> `compile_spec` -> `compile_tests` -> `run_tests`
>    - If tests fail, use `attempt_fix` first
>    - If that fails, read the spec and refine the requirements

---

## See Also

- `README.md` - User documentation and CLI reference
- `ROADMAP.md` - Development phases and future work
- `CONTRIBUTING.md` - Contribution guidelines and required checks
