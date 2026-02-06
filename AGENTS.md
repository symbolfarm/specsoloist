# SpecSoloist for AI Agents

This file provides context for AI agents working with SpecSoloist, whether developing the framework itself or using it as a tool.

> **Note**: `CLAUDE.md` and `GEMINI.md` are symlinks to this file. This ensures all AI agents receive the same context regardless of which file their tooling reads.

---

## Core Concepts

### The Vision: Vibe-Coding

SpecSoloist enables "vibe-coding" - describe what you want in plain English, and the system generates working code:

```
User: "Build me a todo app with auth"
         │
         ▼
   SpecComposer          → Drafts architecture + specs
         │
   [Optional Review]     → User can edit specs
         │
         ▼
   SpecConductor         → Compiles specs in parallel
         │
         ▼
   Working Code + Tests  → Ready to run
```

### The Orchestra Metaphor

The project uses an orchestra metaphor:

| Role | Component | Responsibility |
|------|-----------|----------------|
| **Composer** | `SpecComposer` | Writes the music (drafts specs from plain English) |
| **Conductor** | `SpecConductor` | Leads the orchestra (manages parallel builds, executes workflows) |
| **Soloist** | `SpecSoloistCore` | Individual performer (compiles one spec at a time) |
| **Score** | `score/` directory | The sheet music (specs that define the system itself) |

### Spec Types

Specs are language-agnostic Markdown files. The `type` field determines structure:

| Type | Purpose | Key Sections |
|------|---------|--------------|
| `function` | Single function (full format) | Interface, Behavior, Contract, Examples |
| `type` | Data structure | Schema, Constraints, Examples |
| `bundle` | Multiple trivial functions/types | `yaml:functions`, `yaml:types` blocks |
| `module` | Aggregates for export | Exports list |
| `workflow` | Multi-step execution | `yaml:steps` block |

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
  providers/           # LLM backends (Gemini, Anthropic)

src/spechestra/        # Orchestration package - high-level workflows
  composer.py          # SpecComposer: Plain English → specs
  conductor.py         # SpecConductor: Parallel builds + perform

tests/                 # pytest tests (52 tests)

score/                 # The Score - SpecSoloist's own specs (The Quine)
  prompts/             # Agent prompts (reference/documentation)
  specsoloist.spec.md  # Core package spec
  spechestra.spec.md   # Orchestration package spec
  spec_format.spec.md  # The spec format itself
  ui.spec.md           # UI module spec
  config.spec.md       # Config module spec
  examples/            # Example specs

.claude/agents/        # Native subagents for Claude Code
  compose.md           # Draft architecture from natural language
  conductor.md         # Orchestrate parallel builds
  respec.md            # Reverse-engineer code to specs
  soloist.md           # Compile a single spec

.gemini/agents/        # Native subagents for Gemini CLI
  compose.md           # (same as Claude, different tool names)
  conductor.md
  respec.md
  soloist.md
```

### The Score ("The Quine")

`score/` contains SpecSoloist's own specifications - it describes itself. The goal is for `sp conduct score/` to regenerate the entire `src/` directory.

### Current State (Phase 5: Agent-First Architecture)

**Completed:**
- CLI: `sp compose`, `sp conduct`, `sp perform`, `sp respec`
- Native subagents: `.claude/agents/` and `.gemini/agents/` for agentic workflows
- Score: `ui.spec.md`, `config.spec.md` lifted
- Renamed: `self_hosting/` → `score/`, `lifter.py` → `respec.py`

**Next up (see ROADMAP.md):**
- Agent-first: Convert `sp fix` to use agents
- Quine completion: Lift remaining modules to `score/`

### Native Subagent Architecture

SpecSoloist uses **native subagents** for Claude Code and Gemini CLI. Instead of spawning external processes, the AI delegates to specialized subagents:

```
User: "respec src/parser.py"
         │
         ▼
   Claude/Gemini (main agent)
         │
         └─► respec subagent
               │
               ├── Read source code
               ├── Generate spec
               ├── Run sp validate
               ├── Fix errors
               └── Write output
```

The subagents are defined in `.claude/agents/` and `.gemini/agents/` with agent-specific tool names.

### The Respec Workflow

**Using native subagents (recommended):**
```
> respec src/specsoloist/parser.py to score/parser.spec.md
```
The AI delegates to the `respec` subagent which handles validation and fixes.

**Using CLI directly:**
```bash
uv run sp respec src/specsoloist/parser.py --out score/parser.spec.md
```
This uses a single LLM call without the validation loop.

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
- `ROADMAP.md` - Development phases and next steps (detailed task breakdown)
- `CONTRIBUTING.md` - Contribution guidelines and required checks
- `score/spec_format.spec.md` - The spec format specification
