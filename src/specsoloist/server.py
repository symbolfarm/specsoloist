import os
import sys

# Check if mcp is installed
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: 'mcp' library not found. Please run `pip install mcp` or use `uv run`.")
    sys.exit(1)

from specsoloist.core import SpecSoloistCore

PROJECT_ROOT = os.environ.get("SPEC_ROOT", ".")

# Initialize core
core = SpecSoloistCore(PROJECT_ROOT)

mcp = FastMCP("SpecSoloist")

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

@mcp.tool()
def compile_tests(name: str) -> str:
    """Generate a test suite for the specification using the configured LLM."""
    try:
        return core.compile_tests(name)
    except Exception as e:
        return f"Error compiling tests: {str(e)}"

@mcp.tool()
def run_tests(name: str) -> str:
    """Run the generated tests for a specification."""
    result = core.run_tests(name)
    if result["success"]:
        return f"Tests PASSED:\n{result['output']}"
    else:
        return f"Tests FAILED:\n{result['output']}"

@mcp.tool()
def attempt_fix(name: str) -> str:
    """Attempt to auto-fix a failing component by analyzing test logs."""
    try:
        return core.attempt_fix(name)
    except Exception as e:
        return f"Error attempting fix: {str(e)}"

def main():
    # This entry point is used by the 'specular' CLI command
    mcp.run()

if __name__ == "__main__":
    main()
