import pytest
import subprocess
import os
import shutil
import importlib.util
from typing import List

# These tests are optional and require an LLM API key and external tools.
# Set RUN_LLM_TESTS=1 to run them.
RUN_LLM_TESTS = os.environ.get("RUN_LLM_TESTS", "0") == "1"

def run_sp_command(args: List[str], cwd: str) -> subprocess.CompletedProcess:
    """Helper to run an 'sp' command and return the result."""
    return subprocess.run(
        ["sp"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )

def has_ts_tools() -> bool:
    """Checks if required TypeScript tools are installed."""
    return all(shutil.which(cmd) is not None for cmd in ["node", "npm", "npx"])

def has_torch() -> bool:
    """Checks if PyTorch is installed."""
    return importlib.util.find_spec("torch") is not None

@pytest.mark.skipif(not RUN_LLM_TESTS, reason="LLM tests are disabled by default. Set RUN_LLM_TESTS=1 to enable.")
class TestExamplesBuild:
    """Integration tests that build the examples using the 'sp' CLI."""

    def test_build_math_example(self, tmp_path):
        """Build the math example (Python)."""
        example_dir = os.path.abspath("examples/math")
        # Copy to tmp_path to avoid polluting the workspace
        # We need to create a src directory in tmp_path because 'sp build' expects it
        os.makedirs(tmp_path / "src", exist_ok=True)
        for f in os.listdir(example_dir):
            if f.endswith(".spec.md"):
                shutil.copy(os.path.join(example_dir, f), tmp_path / "src" / f)
        
        # Build all specs in the example
        result = run_sp_command(["build", "--root", str(tmp_path)], cwd=".")
        assert result.returncode == 0, f"Build failed: {result.stdout}\n{result.stderr}"
        assert "Compiled to" in result.stdout
        
        # Run tests for a specific spec
        result = run_sp_command(["test", "math_demo", "--root", str(tmp_path)], cwd=".")
        assert result.returncode == 0, f"Tests failed: {result.stdout}\n{result.stderr}"

    def test_build_user_project_example(self, tmp_path):
        """Build the user_project example (Python)."""
        example_dir = os.path.abspath("examples/user_project")
        shutil.copytree(example_dir, tmp_path, dirs_exist_ok=True)
        
        result = run_sp_command(["build", "--root", str(tmp_path)], cwd=".")
        assert result.returncode == 0, f"Build failed: {result.stdout}\n{result.stderr}"
        
        result = run_sp_command(["test", "user_service", "--root", str(tmp_path)], cwd=".")
        assert result.returncode == 0, f"Tests failed: {result.stdout}\n{result.stderr}"

    @pytest.mark.skipif(not has_ts_tools(), reason="TypeScript tools (node, npm, npx) not found.")
    def test_build_ts_demo_example(self, tmp_path):
        """Build the ts_demo example (TypeScript)."""
        example_dir = os.path.abspath("examples/ts_demo")
        shutil.copytree(example_dir, tmp_path, dirs_exist_ok=True)
        
        # We need an arrangement for TypeScript
        ts_arrangement = os.path.abspath("arrangements/arrangement.typescript.yaml")
        
        result = run_sp_command(["build", "--root", str(tmp_path), "--arrangement", ts_arrangement], cwd=".")
        assert result.returncode == 0, f"Build failed: {result.stdout}\n{result.stderr}"
        
        # Run tests for a specific spec
        result = run_sp_command(["test", "ts_demo", "--root", str(tmp_path), "--arrangement", ts_arrangement], cwd=".")
        assert result.returncode == 0, f"Tests failed: {result.stdout}\n{result.stderr}"

    @pytest.mark.skipif(not has_torch(), reason="PyTorch (torch) is not installed.")
    def test_build_ml_demo_example(self, tmp_path):
        """Build the ml_demo example (PyTorch)."""
        example_dir = os.path.abspath("examples/ml_demo")
        shutil.copytree(example_dir, tmp_path, dirs_exist_ok=True)
        
        result = run_sp_command(["build", "--root", str(tmp_path)], cwd=".")
        assert result.returncode == 0, f"Build failed: {result.stdout}\n{result.stderr}"
        
        result = run_sp_command(["test", "model", "--root", str(tmp_path)], cwd=".")
        assert result.returncode == 0, f"Tests failed: {result.stdout}\n{result.stderr}"
