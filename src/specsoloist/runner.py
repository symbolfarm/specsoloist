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

    def _get_lang_config(self, language: Optional[str]) -> LanguageConfig:
        """Helper to get language config from SpecSoloistConfig."""
        # Default to python if no language specified
        if language is None:
            language = "python"
        if self.config and language in self.config.languages:
            return self.config.languages[language]
        # Fallback to default Python config
        return LanguageConfig()

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

        def read_file(self, filename: str) -> Optional[str]:

            """Reads a file relative to the build directory."""

            path = os.path.join(self.build_dir, filename)

            if not os.path.exists(path):

                # Try absolute or relative to CWD if it exists and is within project root

                if os.path.exists(filename):

                    path = filename

                else:

                    return None

            with open(path, 'r') as f:

                return f.read()

    

        def write_file(self, filename: str, content: str) -> str:

            """

            Writes a file to a specific path.

            If filename is relative, it's relative to build_dir.

            """

            if os.path.isabs(filename):

                target_path = filename

            else:

                target_path = os.path.abspath(os.path.join(self.build_dir, filename))

            

            # Ensure directory exists

            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            

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

            return self._execute_command(cmd, env)

    

        def run_custom_test(self, command: str) -> TestResult:

            """Runs a custom test command (shell)."""

            try:

                # Use shell=True for custom commands which might have pipes/redirects

                result = subprocess.run(

                    command,

                    shell=True,

                    capture_output=True,

                    text=True,

                    check=False

                )

    

                return TestResult(

                    success=result.returncode == 0,

                    output=result.stdout + "\n" + result.stderr,

                    return_code=result.returncode

                )

            except Exception as e:

                return TestResult(

                    success=False,

                    output=f"Execution error: {str(e)}",

                    return_code=-1

                )

    

        def _execute_command(self, cmd: list, env: dict) -> TestResult:

            """Internal helper to execute a command list."""

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

    