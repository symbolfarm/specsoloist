"""Test execution and result handling."""

import os
import subprocess
from dataclasses import dataclass
from typing import Optional

from .config import SpecSoloistConfig, LanguageConfig


@dataclass
class TestResult:
    """Result of a test run."""
    __test__ = False  # prevent pytest collection
    success: bool
    output: str
    return_code: int = 0


class TestRunner:
    """Handles execution of tests for different languages."""
    __test__ = False  # prevent pytest collection

    def __init__(self, build_dir: str, config: Optional[SpecSoloistConfig] = None):
        """Initialize the test runner.

        Args:
            build_dir: Directory where code and tests are built.
            config: SpecSoloist configuration.
        """
        self.build_dir = os.path.abspath(build_dir)
        self.config = config

    def _get_lang_config(self, language: Optional[str]) -> LanguageConfig:
        """Helper to get language config from SpecSoloistConfig."""
        # Default to python if no language specified
        if language is None:
            language = "python"
        if self.config and language in self.config.languages:
            return self.config.languages[language]
        # Fallback to default Python config
        return LanguageConfig(
            extension=".py",
            test_extension=".py",
            test_filename_pattern="test_{name}",
            test_command=["python", "-m", "pytest", "{file}"],
            env_vars={"PYTHONPATH": "{build_dir}"},
        )

    def get_code_path(self, module_name: str, language: str = "python") -> str:
        """Returns the path to the implementation file for a module."""
        cfg = self._get_lang_config(language)
        return os.path.join(self.build_dir, f"{module_name}{cfg.extension}")

    def get_test_path(self, module_name: str, language: str = "python") -> str:
        """Returns the path to the test file for a module."""
        cfg = self._get_lang_config(language)
        filename = cfg.test_filename_pattern.format(name=module_name) + cfg.test_extension
        return os.path.join(self.build_dir, filename)

    def code_exists(self, module_name: str, language: str = "python") -> bool:
        """Checks if an implementation file exists for the module."""
        return os.path.exists(self.get_code_path(module_name, language))

    def test_exists(self, module_name: str, language: str = "python") -> bool:
        """Checks if a test file exists for the module."""
        return os.path.exists(self.get_test_path(module_name, language))

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
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def write_tests(self, module_name: str, content: str, language: str = "python") -> str:
        """Writes test code to the build directory."""
        path = self.get_test_path(module_name, language)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def write_file(self, filename: str, content: str) -> str:
        """Writes a file to the build directory using basename only.

        Prevents path traversal attacks by using only the basename.

        Args:
            filename: Basename of the file to write.
            content: Content to write.

        Returns:
            Absolute path to the written file.
        """
        # Use only basename to prevent path traversal
        basename = os.path.basename(filename)
        target_path = os.path.join(self.build_dir, basename)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, 'w') as f:
            f.write(content)
        return target_path

    def run_tests(self, module_name: str, language: str = "python") -> TestResult:
        """Runs the test command for a module based on its language configuration."""
        cfg = self._get_lang_config(language)
        test_path = self.get_test_path(module_name, language)

        # Verify test file exists
        if not os.path.exists(test_path):
            return TestResult(
                success=False,
                output=f"Test file not found at {test_path}. Compile first.",
                return_code=-1
            )

        # Prepare environment variables
        env = os.environ.copy()
        for k, v in cfg.env_vars.items():
            # Format placeholders and prepend to existing values
            formatted_value = v.format(build_dir=self.build_dir)
            existing_value = env.get(k, "")
            if existing_value:
                env[k] = formatted_value + os.pathsep + existing_value
            else:
                env[k] = formatted_value

        # Determine test file path for command
        actual_test_path = test_path
        if self.config and self.config.sandbox:
            # Inside the container, build_dir is mounted at /app/build
            rel_path = os.path.relpath(test_path, self.build_dir)
            actual_test_path = os.path.join("/app/build", rel_path)

        # Format the test command
        cmd = [part.format(file=actual_test_path) for part in cfg.test_command]

        # Execute command, wrapping with docker if sandboxing enabled
        return self._execute_command(cmd, env)

    def _execute_command(self, cmd: list, env: dict) -> TestResult:
        """Internal helper to execute a command list."""
        try:
            # If sandboxing is enabled, wrap the command in docker run
            if self.config and self.config.sandbox:
                docker_cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{self.build_dir}:/app/build",
                    "-w", "/app",
                ]

                # Pass environment variables to the container
                for k, v in env.items():
                    docker_cmd.extend(["-e", f"{k}={v}"])

                docker_cmd.append(self.config.sandbox_image)
                docker_cmd.extend(cmd)
                cmd = docker_cmd

            result = subprocess.run(
                cmd,
                env=env if not (self.config and self.config.sandbox) else os.environ,
                capture_output=True,
                text=True,
                check=False
            )

            return TestResult(
                success=result.returncode == 0,
                output=result.stdout + result.stderr,
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
