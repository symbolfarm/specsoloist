"""Test execution and file management for SpecSoloist builds."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Optional

from specsoloist.config import LanguageConfig, SpecSoloistConfig


@dataclass
class TestResult:
    """Result of a test execution."""

    success: bool
    output: str
    return_code: int = 0


class TestRunner:
    """Manages the build directory and runs tests."""

    def __init__(
        self, build_dir: str, config: Optional[SpecSoloistConfig] = None
    ) -> None:
        self.build_dir = build_dir
        self.config = config or SpecSoloistConfig()

    def _get_lang_config(self, language: str) -> LanguageConfig:
        """Get language config, falling back to Python."""
        return self.config.languages.get(
            language, self.config.languages.get("python")
        )

    def get_code_path(self, module_name: str, language: str = "python") -> str:
        """Get absolute path to implementation file."""
        lang = self._get_lang_config(language)
        return os.path.join(self.build_dir, f"{module_name}{lang.extension}")

    def get_test_path(self, module_name: str, language: str = "python") -> str:
        """Get absolute path to test file."""
        lang = self._get_lang_config(language)
        test_name = lang.test_filename_pattern.replace("{name}", module_name)
        return os.path.join(self.build_dir, f"{test_name}{lang.test_extension}")

    def code_exists(self, module_name: str, language: str = "python") -> bool:
        """Check if implementation file exists."""
        return os.path.exists(self.get_code_path(module_name, language))

    def test_exists(self, module_name: str, language: str = "python") -> bool:
        """Check if test file exists."""
        return os.path.exists(self.get_test_path(module_name, language))

    def read_code(self, module_name: str, language: str = "python") -> Optional[str]:
        """Read implementation file content."""
        path = self.get_code_path(module_name, language)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return f.read()

    def read_tests(self, module_name: str, language: str = "python") -> Optional[str]:
        """Read test file content."""
        path = self.get_test_path(module_name, language)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return f.read()

    def write_code(self, module_name: str, content: str, language: str = "python") -> str:
        """Write implementation file."""
        path = self.get_code_path(module_name, language)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return path

    def write_tests(self, module_name: str, content: str, language: str = "python") -> str:
        """Write test file."""
        path = self.get_test_path(module_name, language)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return path

    def write_file(self, filename: str, content: str) -> str:
        """Write a file to build dir using basename only."""
        basename = os.path.basename(filename)
        path = os.path.join(self.build_dir, basename)
        os.makedirs(self.build_dir, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return path

    def run_tests(self, module_name: str, language: str = "python") -> TestResult:
        """Run tests for a module."""
        test_path = self.get_test_path(module_name, language)

        if not os.path.exists(test_path):
            return TestResult(
                success=False,
                output=f"Test file not found: {test_path}",
                return_code=1,
            )

        lang = self._get_lang_config(language)

        # Build environment
        env = os.environ.copy()
        if lang.env_vars:
            for key, val in lang.env_vars.items():
                formatted = val.replace("{build_dir}", self.build_dir)
                if key in env and key == "PYTHONPATH":
                    # Prepend to existing PYTHONPATH
                    env[key] = formatted + os.pathsep + env[key]
                else:
                    env[key] = formatted

        # Format test command
        cmd = [
            part.replace("{file}", test_path).replace("{build_dir}", self.build_dir)
            for part in lang.test_command
        ]

        if self.config.sandbox:
            # Wrap in docker run
            docker_env_flags = []
            for key, val in (lang.env_vars or {}).items():
                formatted = val.replace("{build_dir}", "/app/build")
                docker_env_flags.extend(["-e", f"{key}={formatted}"])

            cmd = [
                "docker", "run", "--rm",
                "-v", f"{self.build_dir}:/app/build",
                "-w", "/app",
            ] + docker_env_flags + [self.config.sandbox_image] + cmd

            # Use plain env for docker (it manages its own env)
            env = os.environ.copy()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
            )
            output = result.stdout + result.stderr
            return TestResult(
                success=result.returncode == 0,
                output=output,
                return_code=result.returncode,
            )
        except FileNotFoundError as e:
            return TestResult(
                success=False,
                output=f"Command not found: {e}",
                return_code=1,
            )
        except Exception as e:
            return TestResult(
                success=False,
                output=f"Error running tests: {e}",
                return_code=1,
            )
