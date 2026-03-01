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

docker/                # Dockerfiles for framework and sandboxed execution
  specsoloist.Dockerfile
  sandbox.Dockerfile

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

### Current State (Phase 6: The Quine)

**Phase 5 Completed:**
- ✅ Agent-first CLI: `sp compose`, `sp conduct`, `sp respec`, `sp fix` all default to agent mode
- ✅ Native subagents: `.claude/agents/` and `.gemini/agents/` fully defined
- ✅ Requirements-oriented specs: All modules in `score/` rewritten to describe requirements, not implementation
- ✅ Round-trip validated: resolver, config, manifest regenerated from specs with all tests passing
- ✅ Soloist agents write code directly from specs (agent IS the compiler)

**Phase 6 Completed:**
- ✅ Quine attempt: `sp conduct score/` to regenerate entire `src/` directory with 52+ tests passing

**Current Goal:**
- Phase 7: Robustness & Polish (Arrangement system, Quine diff tool)

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

## See Also

- `README.md` - User documentation and CLI reference
- `ROADMAP.md` - Development phases and next steps (detailed task breakdown)
- `CONTRIBUTING.md` - Contribution guidelines and required checks
- `score/spec_format.spec.md` - The spec format specification
