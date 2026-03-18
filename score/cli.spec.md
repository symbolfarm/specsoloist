---
name: cli
type: bundle
dependencies:
  - core
  - resolver
  - ui
tags:
  - cli
  - user-facing
---

# Overview

Command-line interface for SpecSoloist. Provides the `sp` command with subcommands for managing, compiling, testing, and building specs. Supports both direct LLM API calls and agent-based workflows (via Claude or Gemini CLI).

# Commands

## Global flags

These flags apply to every subcommand and must be specified before the subcommand name:

- `--quiet` — Suppress all non-error output (useful for CI/scripting)
- `--json` — Emit machine-readable JSON instead of Rich terminal output

After parsing args, `ui.configure(quiet=..., json_mode=...)` is called immediately so all subsequent output respects the flags.

## Project Setup

- `sp init [name] [--arrangement python|typescript] [--template NAME] [--list-templates]` — Scaffold a new SpecSoloist project. With `--template`, copies a named arrangement template (e.g. `python-fasthtml`, `nextjs-vitest`, `nextjs-playwright`). With `--list-templates`, prints available templates and exits.

## Spec Management

- `sp list` — List all specs in the project with name, type, status, and description
- `sp create <name> <description> [--type TYPE]` — Create a new spec from template
- `sp validate <name> [--arrangement FILE] [--json]` — Validate a spec's structure; exit 1 if invalid
- `sp verify` — Verify all specs for orchestration readiness (schemas, dependencies, data flow)
- `sp graph` — Export dependency graph as Mermaid diagram
- `sp status [--json]` — Show compilation state of each spec (whether implementation and test files exist in build/)

## Compilation

- `sp compile <name> [--model MODEL] [--no-tests] [--arrangement FILE] [--json]` — Compile a single spec to code (validates first)
- `sp build [--incremental] [--parallel] [--workers N] [--model MODEL] [--no-tests] [--arrangement FILE]` — Compile all specs in dependency order

## Testing & Fixing

- `sp test [name] [--all]` — Run tests for a spec; with `--all`, run tests for every compiled spec; exit 1 if tests fail
- `sp fix <name> [--no-agent] [--auto-accept] [--model MODEL]` — Auto-fix failing tests; defaults to agent-based mode; `--no-agent` uses direct LLM API

## Orchestration

- `sp vibe [brief] [--template NAME] [--pause-for-review] [--resume] [--no-agent] [--auto-accept] [--model MODEL]` — Single-command pipeline: compose specs from a brief, then conduct a build. `brief` may be a `.md` file path or a plain string. `--pause-for-review` pauses after composing so specs can be edited before building. `--resume` treats the brief as an addendum and skips already-compiled specs.
- `sp compose <request> [--no-agent] [--auto-accept] [--model MODEL]` — Draft architecture and specs from natural language description
- `sp conduct [src_dir] [--no-agent] [--auto-accept] [--incremental] [--parallel] [--workers N] [--model MODEL] [--arrangement FILE] [--resume | --force]` — Orchestrate project build using agent or direct LLM. `src_dir` defaults to `src/`. `--resume` skips specs whose hash and output files match the manifest. `--force` recompiles all specs regardless of manifest.
- `sp perform <workflow> <inputs-json>` — Execute a compiled workflow spec with JSON inputs

## Reverse Engineering

- `sp respec <file> [--test TEST] [--out PATH] [--no-agent] [--model MODEL] [--auto-accept]` — Reverse engineer source code to spec

## Diagnostics

- `sp diff <left> [right] [--json] [--label-left LABEL] [--label-right LABEL] [--report PATH] [--runs N]` — Detect spec vs code drift (spec-drift mode: `left` is a spec name) or compare two build directories (build-diff mode: both `left` and `right` are directory paths). `--runs N` compares the last N recorded build runs.
- `sp doctor [--arrangement FILE]` — Check environment health: API keys, agent CLIs, tool availability. With `--arrangement`, also warns about unset required env vars declared in the arrangement.
- `sp install-skills [--target DIR]` — Install SpecSoloist agent skill definitions to the target directory (default `.claude/skills`)

# Behavior

## Agent detection

Commands that support `--no-agent` (compose, conduct, fix, respec, vibe) default to agent-based execution. The CLI detects the available agent CLI (claude or gemini) and delegates to it. If no agent is found or the command is run inside an active agent session, it prints a warning suggesting `--no-agent`.

## Model resolution

For commands that call the LLM, the effective model is resolved with this precedence:
1. `--model` CLI flag
2. `model` field in the arrangement file (if loaded)
3. `SPECSOLOIST_LLM_MODEL` environment variable
4. Provider default

## Arrangement auto-discovery

When no `--arrangement` flag is given, the CLI looks for `arrangement.yaml` in the current directory and then in the project root. If found, it is loaded and applied automatically.

## Error handling

- `CircularDependencyError` and `MissingDependencyError` are caught and displayed as user-friendly error messages
- Keyboard interrupt prints a warning and exits with code 130
- All commands that need LLM access check for the appropriate API key first

## API key checking

Before any LLM operation, validates that the appropriate API key environment variable is set. Supported providers and their key variables: `GEMINI_API_KEY` (gemini/google), `ANTHROPIC_API_KEY` (anthropic), `OPENAI_API_KEY` (openai), `OPENROUTER_API_KEY` (openrouter). Ollama requires no key. Config is loaded from `SPECSOLOIST_LLM_PROVIDER` and `SPECSOLOIST_LLM_MODEL` environment variables.
