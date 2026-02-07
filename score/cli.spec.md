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

## Spec Management

- `sp list` — List all specs in the project with name, type, status, and description
- `sp create <name> <description> [--type TYPE]` — Create a new spec from template
- `sp validate <name>` — Validate a spec's structure; exit 1 if invalid
- `sp verify` — Verify all specs for orchestration readiness (schemas, dependencies, data flow)
- `sp graph` — Export dependency graph as Mermaid diagram

## Compilation

- `sp compile <name> [--model MODEL] [--no-tests]` — Compile a single spec to code (validates first)
- `sp build [--incremental] [--parallel] [--workers N] [--model MODEL] [--no-tests]` — Compile all specs in dependency order

## Testing & Fixing

- `sp test <name>` — Run tests for a spec; exit 1 if tests fail
- `sp fix <name> [--model MODEL]` — Auto-fix failing tests using LLM analysis

## Orchestration

- `sp compose <request> [--no-agent] [--auto-accept]` — Draft architecture and specs from natural language description
- `sp conduct [--incremental] [--parallel] [--workers N] [--model MODEL]` — Orchestrate project build using SpecConductor
- `sp perform <workflow> <inputs-json>` — Execute a workflow spec with JSON inputs

## Reverse Engineering

- `sp respec <file> [--test TEST] [--out PATH] [--no-agent] [--model MODEL] [--auto-accept]` — Reverse engineer source code to spec

## Other

- `sp mcp` — Start the MCP server for AI agent integration

# Behavior

## Agent detection

Commands that support `--no-agent` (compose, respec) default to agent-based execution. The CLI detects the available agent CLI (gemini or claude) and delegates to it via one-shot mode. If no agent is found, it prints an error suggesting `--no-agent`.

## Error handling

- `CircularDependencyError` and `MissingDependencyError` are caught and displayed as user-friendly error messages
- Keyboard interrupt prints a warning and exits with code 130
- All commands that need LLM access check for the appropriate API key first

## API key checking

Before any LLM operation, validates that the appropriate API key environment variable is set based on the configured provider (GEMINI_API_KEY or ANTHROPIC_API_KEY).
