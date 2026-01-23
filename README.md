# Specular

**Specular** is a "Spec-as-Source" AI coding framework. It treats rigorous, SRS-style specifications as the source of truth and uses LLMs (like Google Gemini) to compile them into executable code.

## Key Features

-   **Spec-as-Source**: Code is a build artifact. You edit the Spec, not the Python/JS file.
-   **Contracts over Code**: Define *what* you want (Functional Requirements) and *constraints* (Non-Functional Requirements).
-   **Agent-Native**: Built as a **Model Context Protocol (MCP)** server, making it a powerful skill for AI Agents.
-   **Self-Healing**: Includes an autonomous loop (`attempt_fix`) that analyzes test failures and rewrites code or tests to resolve discrepancies.

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

### Supported Models

Defaults to **Google Gemini 2.0 Flash** for high speed and reasoning capabilities.

## Development

Managed with `uv`.

```bash
uv run specular  # Runs the MCP server
uv run pytest    # Runs the framework's own unit tests
```
