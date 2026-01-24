# Specular

**Specular** is a "Spec-as-Source" AI coding framework. It treats rigorous, SRS-style specifications as the source of truth and uses LLMs (like Google Gemini) to compile them into executable code.

## Key Features

-   **Spec-as-Source**: Code is a build artifact. You edit the Spec, not the Python/JS file.
-   **Contracts over Code**: Define *what* you want (Functional Requirements) and *constraints* (Non-Functional Requirements).
-   **Agent-Native**: Built as a **Model Context Protocol (MCP)** server, making it a powerful skill for AI Agents.
-   **Self-Healing**: Includes an autonomous loop (`attempt_fix`) that analyzes test failures and rewrites code or tests to resolve discrepancies.
-   **Multi-Provider**: Supports multiple LLM backends (Google Gemini, Anthropic Claude) via a pluggable provider system.

## Installation

```bash
# Requires Python 3.10+ and uv
git clone https://github.com/yourusername/specular.git
cd specular
uv sync
```

## Quick Start (Demo)

We have included a robust end-to-end demo that creates a component, generates code/tests, encounters a bug, and **automatically fixes it**.

```bash
export GEMINI_API_KEY="your-key-here"
uv run python3 demo.py
```

## Usage

### As an MCP Server (Recommended for Agents)

Add this to your Claude Desktop or Agent configuration:

```json
"specular": {
  "command": "uv",
  "args": ["run", "specular"],
  "env": {
    "GEMINI_API_KEY": "your-key-here"
  }
}
```

### Supported LLM Providers

Specular supports multiple LLM providers via environment variables:

**Google Gemini (default)**
```bash
export GEMINI_API_KEY="your-key-here"
# Optionally specify model
export SPECULAR_LLM_MODEL="gemini-2.0-flash"
```

**Anthropic Claude**
```bash
export SPECULAR_LLM_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="your-key-here"
# Optionally specify model
export SPECULAR_LLM_MODEL="claude-sonnet-4-20250514"
```

## Development

Managed with `uv`.

```bash
uv run specular  # Runs the MCP server
uv run pytest    # Runs the framework's own unit tests
```
