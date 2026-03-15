# SpecSoloist for AI Agents

This file provides context for AI agents working with SpecSoloist, whether developing the framework itself or using it as a tool.

> **Note**: The canonical file is `AGENTS.md`. `CLAUDE.md` and `GEMINI.md` are symlinks to it — edit `AGENTS.md` directly. This ensures all AI agents receive the same context regardless of which file their tooling reads.

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
| **Arrangement** | Arrangement file | The technical rider (build config, output paths, tools) |
| **Score** | `score/` directory | The sheet music (specs that define the system itself) |

### Spec Philosophy: Requirements, Not Blueprints

Specs define **what** the code should do, not **how** it should do it. The **Arrangement** file defines the **how** (output paths, language, tools).

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
uv run python -m pytest tests/   # Run tests (270 tests)
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
  conductor.py         # SpecConductor: Parallel builds

docker/                # Dockerfiles for framework and sandboxed execution
  specsoloist.Dockerfile
  sandbox.Dockerfile

tests/                 # pytest tests (270 tests)

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
  composer.spec.md     # Architecture drafting
  conductor.spec.md    # Build orchestration
  arrangement.spec.md  # Build configuration schema

src/specsoloist/skills/  # Cross-platform skill definitions (agentskills format)
  sp-compose/SKILL.md    # Same five agents, platform-neutral
  sp-conduct/SKILL.md    # Skills are the source of truth for agent behavior;
  sp-respec/SKILL.md     # native agent files below are platform-specific wrappers
  sp-soloist/SKILL.md    # (different tool names per platform, Gemini adds max_turns)
  sp-fix/SKILL.md

.claude/agents/        # Native subagents for Claude Code (Claude tool names)
  compose.md           # Draft architecture from natural language
  conductor.md         # Orchestrate builds, spawn soloists
  respec.md            # Extract requirements from code -> spec
  soloist.md           # Read spec, write code directly
  fix.md               # Analyze failures, patch code, re-test

.gemini/agents/        # Native subagents for Gemini CLI (Gemini tool names)
  compose.md
  conductor.md
  respec.md
  soloist.md
  fix.md
```

### The Score ("The Quine")

`score/` contains SpecSoloist's own specifications - it describes itself. The goal is for `sp conduct score/` to regenerate the entire `src/` directory with passing tests.

### Current State (Phase 9: Distribution & DX)

**Phases 1–8 Completed.** See `tasks/HISTORY.md` for full history.

**Phase 8 highlights:**
- ✅ `type: reference` spec type for third-party API documentation
- ✅ Arrangement templates (`sp init --template python-fasthtml/nextjs-vitest/nextjs-playwright`)
- ✅ FastHTML + Next.js examples validated end-to-end
- ✅ `sp conduct --resume` / `--force` for incremental builds
- ✅ `env_vars` in arrangements; `sp doctor --arrangement` warns on unset required vars
- ✅ Nested session detection with friendly warning
- ✅ Incremental adoption guide + database persistence patterns
- ✅ 270 tests passing

**Current Goal:**
- Phase 9: Distribution & DX — `sp diff`, `sp vibe`, Pydantic AI providers, quine CI

### Native Subagent Architecture

SpecSoloist uses **native subagents** for Claude Code and Gemini CLI. The architecture differs by platform:

**Claude Code** (`.claude/agents/`): The conductor spawns soloists as parallel Task subagents:

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

**Gemini CLI** (`.gemini/agents/`): Due to the experimental agents subagent limit, the conductor compiles specs directly using its own tools (read/write/shell), optionally delegating to `generalist` for complex specs. The `soloist` agent definition exists for standalone use but is not spawned as a subagent by the conductor.

Each soloist (or the conductor directly) reads the spec file, writes implementation code, writes tests, runs them, and fixes issues — up to 3 retries.

### Running `sp conduct` from Within a Claude Code Session

`sp conduct` (agent mode) works by spawning a new Claude Code subprocess. This is
blocked when already inside an active Claude Code session — the subprocess can't start.

**The right approach when you are already Claude Code:** use the `Agent` tool to spawn
the `conductor` agent directly. No subprocess needed — you *are* the runtime.

```
# Instead of shelling out to:
sp conduct examples/myapp/specs/ --arrangement arrangement.yaml

# Do this from within the session:
Agent(subagent_type="conductor", prompt="Build specs in examples/myapp/specs/ using arrangement.yaml ...")
```

The conductor agent will read the specs, resolve dependencies, and spawn soloist
subagents via the `Agent` tool — exactly what `sp conduct` does from a terminal.

Fallback: `sp conduct --no-agent` uses direct LLM API calls with no subprocess, and
works from within a Claude Code session (requires `ANTHROPIC_API_KEY` or `GEMINI_API_KEY`).

### Before Committing

See `CONTRIBUTING.md` for required checks and conventions.

---

## See Also

- `README.md` - User documentation and CLI reference
- `ROADMAP.md` - Development phases (high-level); `IDEAS.md` - future directions
- `tasks/README.md` - Active task backlog; `tasks/HISTORY.md` - completed work
- `CONTRIBUTING.md` - Contribution guidelines and required checks
- `score/spec_format.spec.md` - The spec format specification
