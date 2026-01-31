"""
Test execution and result handling.
"""

import os
import subprocess
from dataclasses import dataclass
from typing import Optional

from .config import SpecSoloistConfig, LanguageConfig


@dataclass
class TestResult:
    """Result of a test run."""
    success: bool
    output: str
    return_code: int = 0


class TestRunner:
    """
    Handles execution of tests for different languages.
    """

    def __init__(self, build_dir: str, config: Optional[SpecSoloistConfig] = None):
        """
        Initialize the test runner.

        Args:
            build_dir: Directory where code and tests are built.
            config: SpecSoloist configuration.
        """
        self.build_dir = os.path.abspath(build_dir)
        self.config = config

    def _get_lang_config(self, language: str) -> LanguageConfig:
        """Helper to get language config from SpecSoloistConfig."""
        if self.config and language in self.config.languages:
            return self.config.languages[language]

    def get_test_path(self, module_name: str, language: str = "python") -> str:
        """Returns the path to the test file for a module."""
        cfg = self._get_lang_config(language)
        filename = cfg.test_filename_pattern.format(name=module_name) + cfg.test_extension
        return os.path.join(self.build_dir, filename)

    def get_code_path(self, module_name: str, language: str = "python") -> str:
        """Returns the path to the implementation file for a module."""
        cfg = self._get_lang_config(language)
        return os.path.join(self.build_dir, f"{module_name}{cfg.extension}")

    def test_exists(self, module_name: str, language: str = "python") -> bool:
        """Checks if a test file exists for the module."""
        return os.path.exists(self.get_test_path(module_name, language))

    def code_exists(self, module_name: str, language: str = "python") -> bool:
        """Checks if an implementation file exists for the module."""
        return os.path.exists(self.get_code_path(module_name, language))

    def read_code(self, module_name: str, language: str = "python") -> Optional[str]:
        """Reads the implementation file content."""
        path = self.get_code_path(module_name, language)
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            return f.read()

    def read_tests(self, module_name: str, language: str = "python") -> Optional[str]:
        """Reads the test file content."""
        path = self.get_test_path(module_name, language)
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            return f.read()

    def write_code(self, module_name: str, content: str, language: str = "python") -> str:
        """Writes implementation code to the build directory."""
        path = self.get_code_path(module_name, language)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def write_tests(self, module_name: str, content: str, language: str = "python") -> str:
        """Writes test code to the build directory."""
        path = self.get_test_path(module_name, language)
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

    def run_tests(self, module_name: str, language: str = "python") -> TestResult:
        """
        Runs the test command for a module based on its language configuration.
        """
        cfg = self._get_lang_config(language)
        test_path = self.get_test_path(module_name, language)

        if not os.path.exists(test_path):
            return TestResult(
                success=False,
                output=f"Test file not found at {test_path}. Compile first.",
                return_code=-1
            )

        # Prepare environment
        env = os.environ.copy()
        for k, v in cfg.env_vars.items():
            # Inject build_dir if placeholder used
            env[k] = v.format(build_dir=self.build_dir) + os.pathsep + env.get(k, "")

        # Prepare command
        cmd = [part.format(file=test_path) for part in cfg.test_command]

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=False
            )

            return TestResult(
                success=result.returncode == 0,
                output=result.stdout + "\n" + result.stderr,
                return_code=result.returncode
            )
        except FileNotFoundError:
            return TestResult(
                success=False,
                output=f"Command not found: {cmd[0]}",
                return_code=-1
            )
        except Exception as e:
            return TestResult(
                success=False,
                output=f"Execution error: {str(e)}",
                return_code=-1
            )