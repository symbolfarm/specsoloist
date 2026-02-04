# SpecSoloist

**SpecSoloist** is a "Spec-as-Source" AI coding framework. It treats rigorous, SRS-style specifications as the source of truth and uses LLMs to compile them into executable code.

Now with **Spechestra** features: define and run multi-agent orchestration workflows directly from your specs.

## Why SpecSoloist?

Code is often messy, poorly documented, and prone to drift from original requirements. SpecSoloist flips the script:

1.  **Write Specs**: You write high-level, human-readable specifications (Markdown).
2.  **Compile to Code**: SpecSoloist uses LLMs (Gemini/Claude) to implement the spec.
3.  **Self-Healing**: If tests fail, SpecSoloist analyzes the failure and patches the code or tests automatically.
4.  **Orchestrate**: Define complex workflows where agents collaborate, share state, and pause for human input.

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

2.  **Conduct Build**: Compile all components in parallel.
    ```bash
    sp conduct
    ```

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
| `sp conduct` | **Build/Compile project (parallel & incremental)** |
| `sp perform` | **Execute an orchestration workflow** |
| `sp validate` | Check spec structure |
| `sp verify` | Verify schemas and interface compatibility |
| `sp compile` | Compile single spec to code + tests |
| `sp test` | Run tests for a spec |
| `sp fix` | Auto-fix failing tests |
| `sp build` | Alias for `conduct` |
| `sp graph` | Export dependency graph (Mermaid.js) |

## Configuration

You can configure SpecSoloist via environment variables or a `.env` file:

```bash
export SPECSOLOIST_LLM_PROVIDER="gemini"  # or "anthropic"
export SPEC_LLM_MODEL="gemini-2.0-flash"  # optional
```

For Anthropic:

```bash
export SPECSOLOIST_LLM_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="your_key_here"
export SPECSOLOIST_LLM_MODEL="claude-sonnet-4-20250514"  # optional
```

## Agent Integration (MCP)

SpecSoloist can run as an MCP server for Claude Desktop or other AI agents:

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "specsoloist": {
      "command": "uv",
      "args": ["run", "specsoloist-mcp"],
      "env": {
        "GEMINI_API_KEY": "..."
      }
    }
  }
}
```

Or use the CLI: `sp mcp`