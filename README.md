# Specular

**Specular** is a "Spec-as-Source" AI coding framework. It treats rigorous, SRS-style specifications as the source of truth and uses LLMs to compile them into executable code.

## Key Features

-   **Spec-as-Source**: Code is a build artifact. You edit the Spec, not the Python/JS file.
-   **Contracts over Code**: Define *what* you want (Functional Requirements) and *constraints* (Non-Functional Requirements).
-   **Self-Healing**: An autonomous loop (`attempt_fix`) analyzes test failures and patches code to resolve discrepancies.
-   **Multi-Provider**: Supports Google Gemini and Anthropic Claude via a pluggable provider system.
-   **Agent-Native**: Also available as an MCP server for AI agents.

## Installation

```bash
# Requires Python 3.10+ and uv
git clone https://github.com/symbolfarm/specular.git
cd specular
uv sync
```

## Quick Start

```bash
# Set your API key
export GEMINI_API_KEY="your-key-here"

# Create a new spec
specular create calculator "A simple calculator with add and multiply"

# Edit src/calculator.spec.md to define your requirements...

# Compile to code
specular compile calculator

# Run the generated tests
specular test calculator

# If tests fail, auto-fix
specular fix calculator
```

## CLI Reference

```
specular list                     List all specs in src/
specular create <name> <desc>     Create a new spec from template
specular validate <name>          Check spec structure
specular compile <name>           Compile spec to code + tests
specular test <name>              Run tests for a spec
specular fix <name>               Auto-fix failing tests
specular build                    Compile all specs in dependency order
  --incremental                   Only recompile changed specs
  --parallel                      Compile independent specs concurrently
```

## LLM Providers

**Google Gemini (default)**
```bash
export GEMINI_API_KEY="your-key-here"
export SPECULAR_LLM_MODEL="gemini-2.0-flash"  # optional
```

**Anthropic Claude**
```bash
export SPECULAR_LLM_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="your-key-here"
export SPECULAR_LLM_MODEL="claude-sonnet-4-20250514"  # optional
```

## MCP Server (for AI Agents)

Specular can run as an MCP server for Claude Desktop or other AI agents:

```json
"specular": {
  "command": "uv",
  "args": ["run", "specular-mcp"],
  "env": {
    "GEMINI_API_KEY": "your-key-here"
  }
}
```

Or use the CLI: `specular mcp`

## Development

```bash
uv run pytest    # Run tests
uv run ruff check src/  # Lint
```
