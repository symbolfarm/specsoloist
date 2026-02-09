"""
Tests for the runner module.
"""

import os
import tempfile
import textwrap
from pathlib import Path

import pytest

from specsoloist.runner import TestResult, TestRunner
from specsoloist.config import SpecSoloistConfig, LanguageConfig


class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_create_successful_result(self):
        """Test creating a successful TestResult."""
        result = TestResult(success=True, output="All tests passed")
        assert result.success is True
        assert result.output == "All tests passed"
        assert result.return_code == 0

    def test_create_failed_result(self):
        """Test creating a failed TestResult."""
        result = TestResult(success=False, output="Test failed", return_code=1)
        assert result.success is False
        assert result.output == "Test failed"
        assert result.return_code == 1

    def test_default_return_code(self):
        """Test that return_code defaults to 0."""
        result = TestResult(success=True, output="")
        assert result.return_code == 0


class TestTestRunner:
    """Tests for TestRunner class."""

    def test_init_creates_absolute_path(self):
        """Test that __init__ creates absolute path for build_dir."""
        runner = TestRunner(".")
        assert os.path.isabs(runner.build_dir)

    def test_init_with_config(self):
        """Test initialization with config."""
        config = SpecSoloistConfig()
        runner = TestRunner("/tmp", config=config)
        assert runner.config is config

    def test_get_code_path_default_language(self):
        """Test get_code_path with default Python language."""
        runner = TestRunner("/build")
        path = runner.get_code_path("mymodule")
        assert path.endswith("mymodule.py")
        assert path.startswith("/build")

    def test_get_code_path_with_language(self):
        """Test get_code_path with specified language."""
        config = SpecSoloistConfig()
        runner = TestRunner("/build", config=config)
        path = runner.get_code_path("mymodule", "typescript")
        assert path.endswith("mymodule.ts")

    def test_get_test_path_default_language(self):
        """Test get_test_path with default Python language."""
        runner = TestRunner("/build")
        path = runner.get_test_path("mymodule")
        assert path.endswith("test_mymodule.py")
        assert path.startswith("/build")

    def test_get_test_path_with_language(self):
        """Test get_test_path with TypeScript language."""
        config = SpecSoloistConfig()
        runner = TestRunner("/build", config=config)
        path = runner.get_test_path("mymodule", "typescript")
        assert path.endswith("mymodule.test.ts")

    def test_get_test_path_formats_placeholder(self):
        """Test that get_test_path correctly formats {name} placeholder."""
        config = SpecSoloistConfig()
        # Create custom language with different pattern
        config.languages["custom"] = LanguageConfig(
            extension=".custom",
            test_extension=".test.custom",
            test_filename_pattern="spec_{name}",
            test_command=["custom-test", "{file}"]
        )
        runner = TestRunner("/build", config=config)
        path = runner.get_test_path("mymodule", "custom")
        assert "spec_mymodule.test.custom" in path

    def test_code_exists_returns_false_for_missing(self):
        """Test that code_exists returns False for missing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            assert runner.code_exists("nonexistent") is False

    def test_code_exists_returns_true_for_existing(self):
        """Test that code_exists returns True for existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            code_path = runner.get_code_path("mymodule")
            Path(code_path).parent.mkdir(parents=True, exist_ok=True)
            Path(code_path).write_text("code")
            assert runner.code_exists("mymodule") is True

    def test_test_exists_returns_false_for_missing(self):
        """Test that test_exists returns False for missing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            assert runner.test_exists("nonexistent") is False

    def test_test_exists_returns_true_for_existing(self):
        """Test that test_exists returns True for existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            test_path = runner.get_test_path("mymodule")
            Path(test_path).parent.mkdir(parents=True, exist_ok=True)
            Path(test_path).write_text("test")
            assert runner.test_exists("mymodule") is True

    def test_read_code_returns_content(self):
        """Test that read_code returns file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            code_path = runner.get_code_path("mymodule")
            Path(code_path).parent.mkdir(parents=True, exist_ok=True)
            Path(code_path).write_text("def hello():\n    pass")
            content = runner.read_code("mymodule")
            assert content == "def hello():\n    pass"

    def test_read_code_returns_none_for_missing(self):
        """Test that read_code returns None for missing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            content = runner.read_code("nonexistent")
            assert content is None

    def test_read_tests_returns_content(self):
        """Test that read_tests returns file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            test_path = runner.get_test_path("mymodule")
            Path(test_path).parent.mkdir(parents=True, exist_ok=True)
            Path(test_path).write_text("def test_hello():\n    pass")
            content = runner.read_tests("mymodule")
            assert content == "def test_hello():\n    pass"

    def test_read_tests_returns_none_for_missing(self):
        """Test that read_tests returns None for missing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            content = runner.read_tests("nonexistent")
            assert content is None

    def test_write_code_creates_file(self):
        """Test that write_code creates and writes code file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            code_content = "def my_function():\n    return 42"
            path = runner.write_code("mymodule", code_content)
            assert os.path.exists(path)
            assert Path(path).read_text() == code_content

    def test_write_code_returns_path(self):
        """Test that write_code returns the written path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.write_code("mymodule", "code")
            assert path.endswith("mymodule.py")

    def test_write_code_creates_parent_directories(self):
        """Test that write_code creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            code_content = "code"
            path = runner.write_code("mymodule", code_content)
            # Should create directories if needed
            assert os.path.exists(os.path.dirname(path))

    def test_write_tests_creates_file(self):
        """Test that write_tests creates and writes test file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            test_content = "def test_my_function():\n    assert True"
            path = runner.write_tests("mymodule", test_content)
            assert os.path.exists(path)
            assert Path(path).read_text() == test_content

    def test_write_tests_returns_path(self):
        """Test that write_tests returns the written path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.write_tests("mymodule", "test")
            assert "test_mymodule" in path

    def test_write_tests_creates_parent_directories(self):
        """Test that write_tests creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            test_content = "test"
            path = runner.write_tests("mymodule", test_content)
            # Should create directories if needed
            assert os.path.exists(os.path.dirname(path))

    def test_write_file_creates_file(self):
        """Test that write_file creates and writes file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            content = "test content"
            path = runner.write_file("config.json", content)
            assert os.path.exists(path)
            assert Path(path).read_text() == content

    def test_write_file_returns_path(self):
        """Test that write_file returns the written path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.write_file("test.txt", "content")
            assert path.endswith("test.txt")

    def test_write_file_prevents_path_traversal(self):
        """Test that write_file prevents path traversal attacks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            # Try to escape the build directory
            path = runner.write_file("../../../etc/passwd", "malicious")
            # Should write to build_dir, not escape it
            assert path.startswith(tmpdir)
            assert "passwd" in os.path.basename(path)

    def test_write_file_uses_basename_only(self):
        """Test that write_file uses only the basename of the filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.write_file("some/nested/path/config.json", "content")
            # Should only use the basename
            assert os.path.basename(path) == "config.json"

    def test_run_tests_returns_failure_for_missing_test(self):
        """Test that run_tests returns failure when test file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            result = runner.run_tests("nonexistent")
            assert result.success is False
            assert result.return_code == -1
            assert "Test file not found" in result.output

    def test_run_tests_executes_test_command(self):
        """Test that run_tests executes the test command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            # Use a shell command that just exits with 0, avoiding pytest issues
            config.languages["python"].test_command = [
                "sh", "-c", "exit 0"
            ]
            runner = TestRunner(tmpdir, config=config)
            test_path = runner.get_test_path("mymodule")
            Path(test_path).parent.mkdir(parents=True, exist_ok=True)
            Path(test_path).write_text("test content")

            result = runner.run_tests("mymodule")
            assert result.return_code == 0

    def test_run_tests_captures_output(self):
        """Test that run_tests captures stdout and stderr."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            test_path = runner.get_test_path("mymodule")
            Path(test_path).parent.mkdir(parents=True, exist_ok=True)

            # Create a test file that prints something
            test_script = textwrap.dedent("""
                import sys
                print("stdout message")
                sys.stderr.write("stderr message")
                sys.exit(0)
            """)
            Path(test_path).write_text(test_script)

            result = runner.run_tests("mymodule")
            assert "stdout message" in result.output or "stderr message" in result.output

    def test_run_tests_sets_success_on_zero_exit_code(self):
        """Test that success is True when exit code is 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            config.languages["python"].test_command = ["sh", "-c", "exit 0"]
            runner = TestRunner(tmpdir, config=config)
            test_path = runner.get_test_path("mymodule")
            Path(test_path).parent.mkdir(parents=True, exist_ok=True)
            Path(test_path).write_text("test")

            result = runner.run_tests("mymodule")
            assert result.success is True

    def test_run_tests_sets_failure_on_nonzero_exit_code(self):
        """Test that success is False when exit code is non-zero."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            config.languages["python"].test_command = ["sh", "-c", "exit 1"]
            runner = TestRunner(tmpdir, config=config)
            test_path = runner.get_test_path("mymodule")
            Path(test_path).parent.mkdir(parents=True, exist_ok=True)
            Path(test_path).write_text("test")

            result = runner.run_tests("mymodule")
            assert result.success is False
            assert result.return_code == 1

    def test_run_tests_formats_file_placeholder(self):
        """Test that run_tests formats {file} placeholder correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            # Use a command that references the file path
            config.languages["python"].test_command = ["sh", "-c", "[ -f {file} ] && exit 0 || exit 1"]
            runner = TestRunner(tmpdir, config=config)
            test_path = runner.get_test_path("mymodule")
            Path(test_path).parent.mkdir(parents=True, exist_ok=True)
            Path(test_path).write_text("test")

            # The command should be formatted with the test path
            result = runner.run_tests("mymodule")
            # If formatting failed, the file won't exist and command fails
            assert result.return_code == 0

    def test_run_tests_sets_environment_variables(self):
        """Test that run_tests sets environment variables from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            # Use a shell command that checks PYTHONPATH
            config.languages["python"].test_command = [
                "sh", "-c", f"echo $PYTHONPATH | grep -q {tmpdir} && exit 0 || exit 1"
            ]
            runner = TestRunner(tmpdir, config=config)
            test_path = runner.get_test_path("mymodule")
            Path(test_path).parent.mkdir(parents=True, exist_ok=True)
            Path(test_path).write_text("test")

            result = runner.run_tests("mymodule")
            assert result.success is True

    def test_run_tests_prepends_env_vars_to_existing(self):
        """Test that env vars are prepended to existing values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            # Use a shell command that checks if PYTHONPATH contains both paths
            config.languages["python"].test_command = [
                "sh", "-c", "echo $PYTHONPATH | grep -q /original/path && exit 0 || exit 1"
            ]
            runner = TestRunner(tmpdir, config=config)

            # Set an existing PYTHONPATH
            original_pythonpath = os.environ.get("PYTHONPATH", "")
            os.environ["PYTHONPATH"] = "/original/path"

            try:
                test_path = runner.get_test_path("mymodule")
                Path(test_path).parent.mkdir(parents=True, exist_ok=True)
                Path(test_path).write_text("test")

                result = runner.run_tests("mymodule")
                assert result.success is True
            finally:
                if original_pythonpath:
                    os.environ["PYTHONPATH"] = original_pythonpath
                else:
                    os.environ.pop("PYTHONPATH", None)

    def test_run_tests_handles_command_not_found(self):
        """Test that run_tests returns failure for missing command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            # Use a nonexistent command
            config.languages["python"].test_command = [
                "/nonexistent/command/that/does/not/exist", "{file}"
            ]
            runner = TestRunner(tmpdir, config=config)

            test_path = runner.get_test_path("mymodule")
            Path(test_path).parent.mkdir(parents=True, exist_ok=True)
            Path(test_path).write_text("pass")

            result = runner.run_tests("mymodule")
            assert result.success is False
            assert result.return_code == -1
            assert "Command not found" in result.output

    def test_run_tests_handles_execution_errors(self):
        """Test that run_tests handles execution errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            # Use a command that exits with non-zero to simulate error
            config.languages["python"].test_command = ["sh", "-c", "exit 42"]
            runner = TestRunner(tmpdir, config=config)

            test_path = runner.get_test_path("mymodule")
            Path(test_path).parent.mkdir(parents=True, exist_ok=True)
            Path(test_path).write_text("test")

            result = runner.run_tests("mymodule")
            assert result.success is False
            assert result.return_code == 42

    def test_get_lang_config_defaults_to_python(self):
        """Test that _get_lang_config defaults to Python."""
        runner = TestRunner("/build")
        cfg = runner._get_lang_config(None)
        assert cfg.extension == ".py"
        assert cfg.test_filename_pattern == "test_{name}"

    def test_get_lang_config_uses_config_language(self):
        """Test that _get_lang_config uses language from config."""
        config = SpecSoloistConfig()
        runner = TestRunner("/build", config=config)
        cfg = runner._get_lang_config("typescript")
        assert cfg.extension == ".ts"

    def test_get_lang_config_fallback_for_unknown_language(self):
        """Test that _get_lang_config falls back to Python for unknown language."""
        runner = TestRunner("/build")
        cfg = runner._get_lang_config("nonexistent_lang")
        assert cfg.extension == ".py"

    def test_round_trip_write_and_read_code(self):
        """Test writing and reading code works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            original = "def my_function():\n    return 42"
            runner.write_code("mymodule", original)
            read_back = runner.read_code("mymodule")
            assert read_back == original

    def test_round_trip_write_and_read_tests(self):
        """Test writing and reading tests works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            original = "def test_my_function():\n    assert True"
            runner.write_tests("mymodule", original)
            read_back = runner.read_tests("mymodule")
            assert read_back == original

    def test_multiple_modules_isolation(self):
        """Test that multiple modules don't interfere with each other."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            runner.write_code("module1", "code1")
            runner.write_code("module2", "code2")
            assert runner.read_code("module1") == "code1"
            assert runner.read_code("module2") == "code2"

    def test_different_languages_different_paths(self):
        """Test that different languages produce different file paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            runner = TestRunner(tmpdir, config=config)

            py_path = runner.get_code_path("mymodule", "python")
            ts_path = runner.get_code_path("mymodule", "typescript")

            assert py_path != ts_path
            assert py_path.endswith(".py")
            assert ts_path.endswith(".ts")
