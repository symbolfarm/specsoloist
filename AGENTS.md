# SpecSoloist for AI Agents

This file provides context for AI agents working with SpecSoloist, whether developing the framework itself or using it as a tool.

> **Note**: `CLAUDE.md` and `GEMINI.md` are symlinks to this file. This ensures all AI agents receive the same context regardless of which file their tooling reads.

---

## Core Concepts

### The Vision: Vibe-Coding

SpecSoloist enables "vibe-coding" - describe what you want in plain English, and agents generate working code:

```
User: "Build me a todo app with auth"
         |
         v
   SpecComposer          -> Drafts architecture + specs
         |
   [Optional Review]     -> User can edit specs
         |
         v
   SpecConductor         -> Spawns soloist agents per spec
         |
         v
   Working Code + Tests  -> Ready to run
```

### The Orchestra Metaphor

| Role | Component | Responsibility |
|------|-----------|----------------|
| **Composer** | `SpecComposer` | Writes the music (drafts specs from plain English) |
| **Conductor** | `SpecConductor` | Leads the orchestra (resolves dependencies, spawns soloists) |
| **Soloist** | Soloist agent | Individual performer (reads one spec, writes code directly) |
| **Score** | `score/` directory | The sheet music (specs that define the system itself) |

### Spec Philosophy: Requirements, Not Blueprints

Specs define **what** the code should do, not **how** it should do it:

- **Public API**: Names, signatures, return types (these ARE the interface contract)
- **Behavior**: What happens when you call a method, including edge cases
- **Examples**: Inputs and expected outputs
- **No internals**: No private methods, algorithm names, or internal data structures

The quick test: *"Could a competent developer implement this in any language?"*

### Spec Types

Specs are language-agnostic Markdown files. The `type` field determines structure:

| Type | Purpose | When to Use |
|------|---------|-------------|
| `bundle` | Multiple functions/types (default) | Most modules |
| `function` | Single function (full format) | Complex standalone functions |
| `type` | Data structure | Pure data definitions |
| `module` | Aggregates for export | Large modules with many exports |
| `workflow` | Multi-step execution | Orchestration pipelines |

### Key Insight

> **Code is a build artifact. Specs are the source of truth.**

---

## For Agents Developing SpecSoloist

### Key Commands

```bash
uv run python -m pytest tests/   # Run tests (52 tests)
uv run ruff check src/           # Lint (must pass with 0 errors)
```

### Project Structure

```
src/specsoloist/       # Core package - individual spec compilation
  core.py              # SpecSoloistCore orchestrator
  parser.py            # Spec parsing (function, type, bundle, workflow)
  compiler.py          # LLM prompt construction
  runner.py            # Test execution
  resolver.py          # Dependency graph
  config.py            # Configuration
  cli.py               # CLI (sp command)
  schema.py            # Interface validation (Pydantic models)
  manifest.py          # Build manifest tracking
  respec.py            # Code-to-spec reverse engineering
  providers/           # LLM backends (Gemini, Anthropic)

src/spechestra/        # Orchestration package - high-level workflows
  composer.py          # SpecComposer: Plain English -> specs
  conductor.py         # SpecConductor: Parallel builds + perform

tests/                 # pytest tests (52 tests)

score/                 # The Score - SpecSoloist's own specs (The Quine)
  spec_format.spec.md  # The spec format itself
  config.spec.md       # Config module
  resolver.spec.md     # Dependency resolution
  manifest.spec.md     # Build manifest
  parser.spec.md       # Spec parsing
  compiler.spec.md     # LLM prompt construction
  runner.spec.md       # Test execution
  schema.spec.md       # Interface validation
  core.spec.md         # Core orchestrator
  cli.spec.md          # CLI
  ui.spec.md           # Terminal UI
  respec.spec.md       # Reverse engineering
  speccomposer.spec.md # Architecture drafting
  specconductor.spec.md # Build orchestration

.claude/agents/        # Native subagents for Claude Code
  compose.md           # Draft architecture from natural language
  conductor.md         # Orchestrate builds, spawn soloists
  respec.md            # Extract requirements from code -> spec
  soloist.md           # Read spec, write code directly

.gemini/agents/        # Native subagents for Gemini CLI
  compose.md           # (same as Claude, different tool names)
  conductor.md
  respec.md
  soloist.md
```

### The Score ("The Quine")

`score/` contains SpecSoloist's own specifications - it describes itself. The goal is for `sp conduct score/` to regenerate the entire `src/` directory with passing tests.

### Current State (Phase 5: Agent-First Architecture)

**Completed:**
- Agent-first CLI: `sp compose`, `sp conduct`, `sp respec` all default to agent mode
- Native subagents: `.claude/agents/` and `.gemini/agents/` fully defined
- Requirements-oriented specs: All modules in `score/` rewritten to describe requirements, not implementation
- Round-trip validated: resolver, config, manifest regenerated from specs with all tests passing
- Soloist agents write code directly from specs (agent IS the compiler)

**Next up (see ROADMAP.md):**
- Quine attempt: `sp conduct score/` to regenerate `src/`
- Agent-first `sp fix` command

### Native Subagent Architecture

SpecSoloist uses **native subagents** for Claude Code and Gemini CLI:

```
sp conduct score/
         |
         v
   Conductor agent
         |
         +-- Read specs, resolve dependencies
         |
         +-- Level 0: spawn soloists for leaf specs (parallel)
         |     +-> soloist: config
         |     +-> soloist: resolver
         |     +-> soloist: ui
         |
         +-- Level 1: spawn soloists for next level
         |     +-> soloist: manifest
         |     +-> soloist: runner
         |     ...
         |
         +-- Run full test suite
         v
   Report results
```

Each soloist reads the spec file, writes implementation code directly, writes tests, runs them, and fixes issues — up to 3 retries.

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
> 2. **Be Rigorous**: Define requirements clearly — public API, behavior, edge cases, examples.
> 3. **Iterate**:
>    - Create Spec -> `compile_spec` -> `compile_tests` -> `run_tests`
>    - If tests fail, use `attempt_fix` first
>    - If that fails, read the spec and refine the requirements

---

## See Also

- `README.md` - User documentation and CLI reference
- `ROADMAP.md` - Development phases and next steps (detailed task breakdown)
- `CONTRIBUTING.md` - Contribution guidelines and required checks
- `score/spec_format.spec.md` - The spec format specification
