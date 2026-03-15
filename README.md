# SpecSoloist

**SpecSoloist** is a "Spec-as-Source" AI coding framework. It treats specifications as the source of truth and uses AI agents to compile them into executable code.

Now with **Spechestra** features: compose systems from natural language, conduct parallel builds, and orchestrate multi-step workflows.

## Why SpecSoloist?

Code is often messy, poorly documented, and prone to drift from original requirements. SpecSoloist flips the script:

1.  **Write Specs**: You write requirements-oriented specifications (Markdown).
2.  **Compile to Code**: AI agents read your specs and write implementations directly.
3.  **Self-Healing**: If tests fail, agents analyze the failure and patch the code.
4.  **Orchestrate**: Define complex workflows where agents collaborate, share state, and pause for human input.

> **Code is a build artifact. Specs are the source of truth.**

## Installation

```bash
pip install specsoloist
```

## Quick Start

1.  Set your API Key (Gemini or Anthropic):
    ```bash
    export GEMINI_API_KEY="your_key_here"
    # or
    export ANTHROPIC_API_KEY="your_key_here"
    ```

2.  Scaffold a new project:
    ```bash
    sp init my-app                                  # blank Python arrangement
    sp init my-app --template python-fasthtml       # FastHTML + pytest
    sp init my-app --template nextjs-vitest         # Next.js + vitest
    sp init my-app --template nextjs-playwright     # Next.js + Playwright E2E
    sp init --list-templates                        # see all options
    ```

3.  Write a brief and vibe:
    ```bash
    cd my-app
    sp vibe "A todo app with auth"          # compose → conduct in one command
    sp vibe brief.md                        # read brief from a Markdown file
    sp vibe brief.md --pause-for-review     # pause to edit specs before building
    sp vibe brief.md --resume               # treat brief as addendum (skip compiled specs)
    ```

    Or run the steps separately:
    ```bash
    sp compose "A todo app with auth"       # draft specs
    sp conduct specs/                       # build
    ```

### Manual workflow (single spec)

```bash
sp create calculator "A simple calculator with add and multiply"
sp compile calculator
sp test calculator
sp fix calculator  # if tests fail
```

## Orchestration (Spechestra)

SpecSoloist allows you to chain multiple specs into a workflow.

1.  **Draft Architecture**: Use `sp compose` to vibe-code your system.
    ```bash
    sp compose "A data pipeline that fetches stocks and calculates SMA"
    ```
    This generates a component architecture and draft specs.

2.  **Conduct Build**: Compile all components via agent orchestration.
    ```bash
    sp conduct
    ```
    The conductor agent resolves dependency order and spawns soloist agents to compile each spec in parallel.

## Adding SpecSoloist to an Existing Project

Already have a FastHTML or Next.js app? You don't have to start over. `sp respec` extracts
specs from your existing code, and the spec layer can coexist with hand-written code indefinitely.

See the [Incremental Adoption Guide](docs/incremental-adoption.md) for a step-by-step walkthrough,
and `examples/fasthtml_incremental/` for a concrete before/after example.

```bash
sp respec src/mymodule.py     # extract a spec from existing code
sp validate specs/mymodule.spec.md
sp conduct specs/mymodule.spec.md --arrangement arrangement.yaml
```

## CLI Reference

| Command | Description |
| :--- | :--- |
| `sp init [name]` | Scaffold a new project (`--template`, `--list-templates`) |
| `sp vibe [brief]` | **Single-command pipeline: compose → conduct** (`--pause-for-review`, `--resume`) |
| `sp compose` | Draft architecture & specs from natural language |
| `sp conduct [dir]` | Build project via conductor/soloist agents |
| `sp respec` | **Reverse engineer code to spec** |
| `sp fix` | **Auto-fix failing tests (Agent-first)** |
| `sp validate` | Check spec structure |
| `sp status` | Show compilation state of each spec |
| `sp doctor` | Check environment health (API keys, CLIs, tools, env vars) |
| `sp compile` | Compile single spec to code + tests |
| `sp test [--all]` | Run tests for a spec (or all compiled specs) |
| `sp diff` | Compare spec against compiled implementation (drift detection) |
| `sp build` | Compile all specs (direct LLM, no agents) |
| `sp list` | List all specs |
| `sp create` | Create a new spec manually |
| `sp graph` | Export dependency graph (Mermaid.js) |
| `sp verify` | Verify schemas and interface compatibility |

Commands that use agents (`vibe`, `compose`, `conduct`, `respec`, `fix`) default to detecting an available agent CLI (Claude Code or Gemini CLI). Use `--no-agent` to fall back to direct LLM API calls.

> **Running inside Claude Code?** `sp conduct` spawns a Claude subprocess, which is blocked inside an active Claude Code session. If you see a "Heads Up" warning, either open a separate terminal, use `--no-agent`, or use the `Agent` tool to spawn the conductor directly (see `AGENTS.md`).

## Configuration

You can configure SpecSoloist via environment variables or a `.env` file:

```bash
export SPECSOLOIST_LLM_PROVIDER="gemini"  # or "anthropic"
export SPECSOLOIST_LLM_MODEL="gemini-2.0-flash"  # optional
```

## Arrangement Files

An **Arrangement** is SpecSoloist's makefile — it bridges language-agnostic specs to a concrete build environment by specifying the target language, output paths, build commands, and constraints.

`sp init --template <name>` copies a validated starter arrangement into your project. Run `sp init --list-templates` to see what's available. You can also start from one of the examples in `arrangements/`:

See `arrangements/arrangement.python.yaml` for a complete example:

```yaml
target_language: python
output_paths:
  implementation: src/mymodule.py
  tests: tests/test_mymodule.py
environment:
  tools: [uv, ruff, pytest]
  setup_commands: [uv sync]
build_commands:
  lint: uv run ruff check .
  test: uv run pytest
constraints:
  - Must use type hints for all public function signatures
```

**Usage:**

```bash
# Explicit path
sp compile myspec --arrangement arrangement.yaml
sp build --arrangement arrangement.yaml
sp conduct --no-agent --arrangement arrangement.yaml

# Auto-discovery: place arrangement.yaml in your project root
# and it will be picked up automatically
sp compile myspec
```

## External Dependencies

Specs describe *your* code. External libraries are inputs to the build. There are three patterns depending on how well the LLM knows the library:

### 1. Well-known libraries — constraints only

For React, pytest, lodash, etc. the soloist already knows the API. Just mention it in the arrangement or spec constraints:

```yaml
constraints:
  - Use React hooks (useState, useEffect) for state management
  - Use Tailwind CSS for styling
```

### 2. Obscure or new libraries — reference spec

For newer libraries (e.g. FastHTML) where LLMs may hallucinate the API, write a
`type: reference` spec documenting the subset you actually use. No code is generated —
the spec body is injected as context into every dependent soloist's prompt:

```markdown
---
name: fasthtml_interface
type: reference
---
# Overview
FastHTML is a Python web framework. Package: `python-fasthtml`. Import: `from fasthtml.common import *`.

# API
## Components
- `Div(**attrs, *children)` — renders a div
- `Form(hx_post, hx_swap, *children)` — HTMX-enabled form
- `Input(name, type, placeholder)` — form input

## App
- `@rt(path)` — route decorator
- `serve()` — start dev server

# Verification
```python
from fasthtml.common import Div, Form, Input
assert callable(Div)
```
```

### 3. Complex SDKs — adapter spec

For SDKs with many moving parts (e.g. Vercel AI SDK), write a thin adapter spec that wraps the SDK. Everything else in your project depends on *your adapter*, not the SDK directly. If you swap the underlying SDK, only the adapter spec changes:

```markdown
---
name: ai_client
type: bundle
dependencies: []
---
# AI Client

Wraps the Vercel AI SDK for this project.

## `streamChat(messages, options)`
Streams a chat completion using `streamText()` from the `ai` package.
Returns an AI SDK `StreamingTextResponse`.
```

See `examples/` for concrete interface and adapter spec examples.

## Sandboxed Execution (Docker)

For safety, SpecSoloist can run generated code and tests inside an isolated Docker container.

1.  **Build the sandbox image**:
    ```bash
    docker build -t specsoloist-sandbox -f docker/sandbox.Dockerfile .
    ```

2.  **Enable sandboxing**:
    ```bash
    export SPECSOLOIST_SANDBOX=true
    # Optional: override the image (default: specsoloist-sandbox)
    # export SPECSOLOIST_SANDBOX_IMAGE="my-custom-image"
    ```

3.  **Run tests**:
    `sp test my_module` will now wrap execution in `docker run`.

For Anthropic:

```bash
export SPECSOLOIST_LLM_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="your_key_here"
export SPECSOLOIST_LLM_MODEL="claude-sonnet-4-20250514"  # optional
```

## Native Subagents (Claude & Gemini)

For the full agentic experience, SpecSoloist provides native subagent definitions for Claude Code and Gemini CLI. These allow the AI to delegate tasks to specialized agents:

| Agent | Purpose |
|-------|---------|
| `compose` | Draft architecture and specs from natural language |
| `conductor` | Orchestrate builds — resolves dependencies, spawns soloists |
| `soloist` | Compile a single spec — reads spec, writes code directly |
| `respec` | Extract requirements from code into specs |
| `fix` | Analyze failures, patch code, and re-test |

**Usage with Claude Code:**
```
> conduct score/
> respec src/specsoloist/parser.py to score/parser.spec.md
```

**Usage with Gemini CLI:**
```
> compose a todo app with user auth
```

The subagent definitions are in `.claude/agents/` and `.gemini/agents/`.
