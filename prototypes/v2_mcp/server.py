from typing import Any
import os
import sys

# Check if mcp is installed, if not, provide a stub/explanation
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: 'mcp' library not found. Please install it using `pip install mcp`.")
    print("This server file is a reference implementation.")
    sys.exit(1)

from core import SpecularCore

# Initialize the Core Logic
# We assume this server is run from the project root or the prototype directory
ROOT_DIR = os.environ.get("SPECULAR_ROOT", ".")
core = SpecularCore(ROOT_DIR)

# Initialize MCP Server
mcp = FastMCP("Specular Framework")

@mcp.tool()
def list_specs() -> list[str]:
    """List all available specification files in the project."""
    return core.list_specs()

@mcp.tool()
def read_spec(name: str) -> str:
    """Read the content of a specific specification file."""
    try:
        return core.read_spec(name)
    except FileNotFoundError:
        return "Error: Spec not found."

@mcp.tool()
def create_spec(name: str, description: str, type: str = "function") -> str:
    """Create a new specification file from the standard template."""
    try:
        return core.create_spec(name, description, type)
    except Exception as e:
        return f"Error creating spec: {str(e)}"

@mcp.tool()
def validate_spec(name: str) -> str:
    """Validate a specification against the SRS standard."""
    result = core.validate_spec(name)
    if result["valid"]:
        return "Spec is VALID."
    else:
        return f"Spec is INVALID. Errors: {result['errors']}"

@mcp.tool()
def compile_spec(name: str) -> str:
    """Compile a specification into source code using the configured LLM."""
    try:
        return core.compile_spec(name)
    except Exception as e:
        return f"Error compiling spec: {str(e)}"

if __name__ == "__main__":
    # Standard MCP entry point
    mcp.run()
