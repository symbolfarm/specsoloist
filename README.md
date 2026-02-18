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

1.  Clone the repository (or create a new folder):
    ```bash
    git clone https://github.com/symbolfarm/specsoloist.git
    cd specsoloist
    ```

2.  Set your API Key (Gemini or Anthropic):
    ```bash
    export GEMINI_API_KEY="your_key_here"
    # or
    export ANTHROPIC_API_KEY="your_key_here"
    ```

3.  Create a new specification:
    ```bash
    sp create calculator "A simple calculator with add and multiply"
    ```
    This creates `src/calculator.spec.md`.

4.  Compile it to code:
    ```bash
    sp compile calculator
    ```
    This generates `build/calculator.py` and `build/test_calculator.py`.

5.  Run the tests:
    ```bash
    sp test calculator
    ```

6.  (Optional) If tests fail, try auto-fix:
    ```bash
    sp fix calculator
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

3.  **Perform Workflow**: Execute a workflow spec.
    ```bash
    sp perform my_workflow '{"symbol": "AAPL"}'
    ```

## CLI Reference

| Command | Description |
| :--- | :--- |
| `sp list` | List all specs in `src/` |
| `sp create` | Create a new spec manually |
| `sp compose` | **Draft architecture & specs from natural language** |
| `sp conduct [dir]` | **Build project via conductor/soloist agents** |
| `sp perform` | **Execute an orchestration workflow** |
| `sp validate` | Check spec structure |
| `sp verify` | Verify schemas and interface compatibility |
| `sp compile` | Compile single spec to code + tests |
| `sp test` | Run tests for a spec |
| `sp fix` | **Auto-fix failing tests (Agent-first)** |
| `sp respec` | **Reverse engineer code to spec** |
| `sp build` | Compile all specs (direct LLM, no agents) |
| `sp graph` | Export dependency graph (Mermaid.js) |

Commands that use agents (`compose`, `conduct`, `respec`, `fix`) default to detecting an available agent CLI (Claude Code or Gemini CLI). Use `--no-agent` to fall back to direct LLM API calls.

## Configuration

You can configure SpecSoloist via environment variables or a `.env` file:

```bash
export SPECSOLOIST_LLM_PROVIDER="gemini"  # or "anthropic"
export SPEC_LLM_MODEL="gemini-2.0-flash"  # optional
```

## Arrangement Files

An **Arrangement** is SpecSoloist's makefile — it bridges language-agnostic specs to a concrete build environment by specifying the target language, output paths, build commands, and constraints.

Copy `arrangement.example.yaml` and customise it for your project:

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
