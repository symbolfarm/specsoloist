# Specular

**Specular** is a "Spec-as-Source" AI coding framework. It treats rigorous, SRS-style specifications as the source of truth and uses LLMs (like Google Gemini) to compile them into executable code.

## Philosophy

1.  **Spec is Source**: Code is a build artifact. You edit the Spec, not the Python/JS file.
2.  **Contracts over Code**: Define *what* you want (Functional Requirements) and *constraints* (Non-Functional Requirements), not just how to do it.
3.  **Agent-Native**: Designed to be used by AI Agents (via MCP) as much as humans.

## Installation

```bash
pip install specular-ai
```

## Usage

### As an MCP Server (Recommended for Agents)

Add this to your Claude Desktop or Agent configuration:

```json
"specular": {
  "command": "specular",
  "env": {
    "GEMINI_API_KEY": "your-key-here"
  }
}
```

### Supported Models

Currently defaults to **Google Gemini 1.5 Flash** for speed and cost-efficiency.

## Development

Managed with `uv`.

```bash
uv sync
uv run specular
```