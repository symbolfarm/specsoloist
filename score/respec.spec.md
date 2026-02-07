---
name: respec
type: bundle
dependencies:
  - config
tags:
  - core
  - reverse-engineering
---

# Overview

Reverse-engineers source code into SpecSoloist specifications using a single-shot LLM call. This is the fallback implementation used with `--no-agent`; the preferred approach is agent-based (see `.claude/agents/respec.md`).

# Types

## Respecer

Reverse engineering tool. Constructed with optional `config` (defaults to environment config) and optional `provider` (defaults to provider created from config).

# Functions

## Respecer.respec(source_path, test_path=None, model=None) -> string

Generate a spec from source code.

**Behavior:**
- Verify source_path exists; raise `FileNotFoundError` if missing
- Read the source code
- Load spec format rules from `score/spec_format.spec.md` relative to config root (if file exists)
- If test_path is provided and exists, read it as additional context
- Construct a prompt instructing the LLM to analyze the code and produce a requirements-oriented spec
- Call the LLM provider and return the cleaned response (markdown fences stripped)
