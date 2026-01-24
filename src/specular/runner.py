"""
Test execution and result handling.
"""

import os
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class TestResult:
    """Result of a test run."""
    success: bool
    output: str
    return_code: int


class TestRunner:
    """Handles test execution for compiled specs."""

    def __init__(self, build_dir: str):
        self.build_dir = os.path.abspath(build_dir)

    def get_test_path(self, module_name: str) -> str:
        """Returns the path to the test file for a module."""
        return os.path.join(self.build_dir, f"test_{module_name}.py")

    def get_code_path(self, module_name: str) -> str:
        """Returns the path to the implementation file for a module."""
        return os.path.join(self.build_dir, f"{module_name}.py")

    def test_exists(self, module_name: str) -> bool:
        """Checks if a test file exists for the module."""
        return os.path.exists(self.get_test_path(module_name))

    def code_exists(self, module_name: str) -> bool:
        """Checks if an implementation file exists for the module."""
        return os.path.exists(self.get_code_path(module_name))

    def read_code(self, module_name: str) -> Optional[str]:
        """Reads the implementation file content."""
        path = self.get_code_path(module_name)
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            return f.read()

    def read_tests(self, module_name: str) -> Optional[str]:
        """Reads the test file content."""
        path = self.get_test_path(module_name)
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            return f.read()

    def write_code(self, module_name: str, content: str) -> str:
        """Writes implementation code to the build directory."""
        path = self.get_code_path(module_name)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def write_tests(self, module_name: str, content: str) -> str:
        """Writes test code to the build directory."""
        path = self.get_test_path(module_name)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def write_file(self, filename: str, content: str) -> str:
        """
        Writes a file to the build directory.
        Security: Only allows writing to build_dir (no path traversal).
        """
        # Security check: ensure we only write to build dir
        clean_name = os.path.basename(filename)
        target_path = os.path.join(self.build_dir, clean_name)
        with open(target_path, 'w') as f:
            f.write(content)
        return target_path

    def run_tests(self, module_name: str) -> TestResult:
        """
        Runs pytest on the test file for a module.
        Returns a TestResult with success status and output.
        """
        test_path = self.get_test_path(module_name)

        if not os.path.exists(test_path):
            return TestResult(
                success=False,
                output="Test file not found. Run compile_tests() first.",
                return_code=-1
            )

        # Set up environment with build_dir in PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = self.build_dir + os.pathsep + env.get("PYTHONPATH", "")

        try:
            result = subprocess.run(
                ["pytest", test_path],
                env=env,
                capture_output=True,
                text=True,
                check=False  # We handle return code manually
            )

            return TestResult(
                success=result.returncode == 0,
                output=result.stdout + "\n" + result.stderr,
                return_code=result.returncode
            )
        except FileNotFoundError:
            return TestResult(
                success=False,
                output="pytest command not found. Is pytest installed?",
                return_code=-1
            )
