# Specular MCP Server (Prototype v2)

This directory contains the reference implementation for the **Specular MCP Server**.

## Structure

- `core.py`: The Python logic that implements the Spec-as-Source framework (Managing specs, validating, compiling). It has NO external dependencies beyond the standard library.
- `server.py`: The MCP wrapper. It exposes the core logic as MCP Tools (`create_spec`, `compile_spec`, etc.).

## Prerequisites

To run the server, you need:
1.  Python 3.10+
2.  The `mcp` library: `pip install mcp`
3.  A Google Gemini API Key: `export GEMINI_API_KEY="your_key"`

## How to Run

1.  Navigate to this directory:
    ```bash
    cd prototypes/v2_mcp
    ```

2.  Run the MCP Server (Stdio Mode):
    ```bash
    python server.py
    ```
    *Note: You normally don't run this manually. You configure your MCP Client (like Claude Desktop or a custom Agent) to run this command.*

## Usage with an Agent

Once connected, the Agent will see the following tools:

- `list_specs()`
- `read_spec(name)`
- `create_spec(name, description)`
- `validate_spec(name)`
- `compile_spec(name)`

The Agent can then act as the "Architect" using these tools to build the software defined in your specs.
