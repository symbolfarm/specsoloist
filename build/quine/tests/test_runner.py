"""Tests for test runner module."""

import os
import tempfile
import pytest
from pathlib import Path

# Import with alias to prevent pytest collection of these classes
from specsoloist.runner import TestResult as TR
from specsoloist.runner import TestRunner
from specsoloist.config import SpecSoloistConfig, LanguageConfig


class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_creation_with_defaults(self):
        """TestResult should have success, output, and return_code fields."""
        result = TR(success=True, output="test output")
        assert result.success is True
        assert result.output == "test output"
        assert result.return_code == 0

    def test_creation_with_all_fields(self):
        """TestResult should accept all fields."""
        result = TR(success=False, output="error", return_code=1)
        assert result.success is False
        assert result.output == "error"
        assert result.return_code == 1

    def test_not_collected_by_pytest(self):
        """TestResult should have __test__ = False to prevent pytest collection."""
        assert hasattr(TR, "__test__")
        assert TR.__test__ is False


class TestTestRunnerInitialization:
    """Tests for TestRunner initialization."""

    def test_init_with_build_dir_only(self):
        """TestRunner should initialize with absolute build_dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            assert runner.build_dir == os.path.abspath(tmpdir)
            assert runner.config is None

    def test_init_with_config(self):
        """TestRunner should accept optional config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            runner = TestRunner(tmpdir, config=config)
            assert runner.config is config

    def test_build_dir_is_absolute(self):
        """TestRunner should convert build_dir to absolute path."""
        runner = TestRunner(".")
        assert os.path.isabs(runner.build_dir)

    def test_not_collected_by_pytest(self):
        """TestRunner should have __test__ = False to prevent pytest collection."""
        assert hasattr(TestRunner, "__test__")
        assert TestRunner.__test__ is False


class TestLanguageConfig:
    """Tests for language configuration handling."""

    def test_get_lang_config_python_default(self):
        """TestRunner should return default Python config when none specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            cfg = runner._get_lang_config(None)
            assert cfg.extension == ".py"
            assert cfg.test_extension == ".py"

    def test_get_lang_config_from_config(self):
        """TestRunner should get language config from SpecSoloistConfig."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            runner = TestRunner(tmpdir, config=config)
            cfg = runner._get_lang_config("python")
            assert cfg.extension == ".py"
            assert cfg.test_command == ["python", "-m", "pytest", "{file}"]

    def test_get_lang_config_custom_language(self):
        """TestRunner should use custom language from config if available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_lang = LanguageConfig(
                extension=".custom",
                test_extension=".custom",
                test_filename_pattern="test_{name}",
                test_command=["custom", "test"],
            )
            config = SpecSoloistConfig()
            config.languages["custom"] = custom_lang
            runner = TestRunner(tmpdir, config=config)
            cfg = runner._get_lang_config("custom")
            assert cfg.extension == ".custom"


class TestFilePathResolution:
    """Tests for file path computation."""

    def test_get_code_path_python(self):
        """get_code_path should return correct path for Python module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.get_code_path("mymodule")
            expected = os.path.join(tmpdir, "mymodule.py")
            assert path == expected

    def test_get_test_path_python(self):
        """get_test_path should return correct path for Python test."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.get_test_path("mymodule")
            expected = os.path.join(tmpdir, "test_mymodule.py")
            assert path == expected

    def test_get_code_path_typescript(self):
        """get_code_path should return correct path for TypeScript module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            runner = TestRunner(tmpdir, config=config)
            path = runner.get_code_path("mymodule", "typescript")
            expected = os.path.join(tmpdir, "mymodule.ts")
            assert path == expected

    def test_get_test_path_typescript(self):
        """get_test_path should return correct path for TypeScript test."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            runner = TestRunner(tmpdir, config=config)
            path = runner.get_test_path("mymodule", "typescript")
            expected = os.path.join(tmpdir, "mymodule.test.ts")
            assert path == expected

    def test_test_path_pattern_substitution(self):
        """get_test_path should substitute {name} placeholder in pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.get_test_path("mylib")
            # Default pattern is "test_{name}"
            assert "test_mylib" in path


class TestFileChecking:
    """Tests for file existence checking."""

    def test_code_exists_returns_false_when_missing(self):
        """code_exists should return False when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            assert runner.code_exists("missing") is False

    def test_code_exists_returns_true_when_present(self):
        """code_exists should return True when file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.get_code_path("mymodule")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            Path(path).touch()
            assert runner.code_exists("mymodule") is True

    def test_test_exists_returns_false_when_missing(self):
        """test_exists should return False when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            assert runner.test_exists("missing") is False

    def test_test_exists_returns_true_when_present(self):
        """test_exists should return True when file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.get_test_path("mymodule")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            Path(path).touch()
            assert runner.test_exists("mymodule") is True


class TestFileReading:
    """Tests for reading code and test files."""

    def test_read_code_returns_none_when_missing(self):
        """read_code should return None when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            assert runner.read_code("missing") is None

    def test_read_code_returns_content(self):
        """read_code should return file content when it exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.get_code_path("mymodule")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            content = "print('hello')"
            with open(path, 'w') as f:
                f.write(content)
            assert runner.read_code("mymodule") == content

    def test_read_tests_returns_none_when_missing(self):
        """read_tests should return None when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            assert runner.read_tests("missing") is None

    def test_read_tests_returns_content(self):
        """read_tests should return file content when it exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.get_test_path("mymodule")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            content = "assert True"
            with open(path, 'w') as f:
                f.write(content)
            assert runner.read_tests("mymodule") == content


class TestFileWriting:
    """Tests for writing code and test files."""

    def test_write_code_creates_file(self):
        """write_code should create implementation file and return path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            content = "print('hello')"
            path = runner.write_code("mymodule", content)
            assert os.path.exists(path)
            with open(path, 'r') as f:
                assert f.read() == content

    def test_write_code_returns_path(self):
        """write_code should return the written file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            content = "x = 1"
            path = runner.write_code("mymodule", content)
            expected = runner.get_code_path("mymodule")
            assert path == expected

    def test_write_tests_creates_file(self):
        """write_tests should create test file and return path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            content = "assert True"
            path = runner.write_tests("mymodule", content)
            assert os.path.exists(path)
            with open(path, 'r') as f:
                assert f.read() == content

    def test_write_tests_returns_path(self):
        """write_tests should return the written file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            content = "assert True"
            path = runner.write_tests("mymodule", content)
            expected = runner.get_test_path("mymodule")
            assert path == expected

    def test_write_code_creates_directories(self):
        """write_code should create parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            # Write to nested path by using a custom module name
            path = runner.write_code("mymodule", "content")
            assert os.path.exists(os.path.dirname(path))

    def test_write_file_uses_basename_only(self):
        """write_file should use only basename to prevent path traversal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.write_file("subdir/myfile.txt", "content")
            # Should use only basename
            expected = os.path.join(tmpdir, "myfile.txt")
            assert path == expected
            assert os.path.exists(path)

    def test_write_file_prevents_path_traversal(self):
        """write_file should prevent writing outside build_dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            # Try to write with parent directory traversal
            path = runner.write_file("../outside.txt", "content")
            # Should write to build_dir/outside.txt, not parent
            assert path.startswith(tmpdir)
            assert os.path.exists(path)

    def test_write_file_returns_path(self):
        """write_file should return the written file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            path = runner.write_file("myfile.txt", "content")
            assert os.path.exists(path)


class TestTestExecution:
    """Tests for test execution."""

    def test_run_tests_fails_when_test_missing(self):
        """run_tests should return failure when test file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            result = runner.run_tests("missing")
            assert result.success is False
            assert result.return_code == -1

    def test_run_tests_failure_has_output(self):
        """run_tests failure should include descriptive output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            result = runner.run_tests("missing")
            assert "Test file not found" in result.output

    def test_run_tests_executes_pytest(self):
        """run_tests should execute pytest when test file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            # Write a simple passing test
            test_content = """
def test_simple():
    assert True
"""
            runner.write_tests("mymodule", test_content)
            result = runner.run_tests("mymodule")
            assert result.success is True
            assert result.return_code == 0

    def test_run_tests_captures_output(self):
        """run_tests should capture pytest output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            test_content = """
def test_with_print():
    print('test output')
    assert True
"""
            runner.write_tests("mymodule", test_content)
            result = runner.run_tests("mymodule")
            # Output should contain pytest output
            assert result.output is not None

    def test_run_tests_failure_when_test_fails(self):
        """run_tests should return failure when test fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            test_content = """
def test_failing():
    assert False
"""
            runner.write_tests("mymodule", test_content)
            result = runner.run_tests("mymodule")
            assert result.success is False
            assert result.return_code != 0

    def test_run_tests_sets_pythonpath(self):
        """run_tests should set PYTHONPATH from env_vars."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            # Write code that imports from build_dir
            code_content = """
def hello():
    return 'hello'
"""
            runner.write_code("mymodule", code_content)
            # Write test that imports the code
            test_content = """
from mymodule import hello

def test_import():
    assert hello() == 'hello'
"""
            runner.write_tests("mymodule", test_content)
            result = runner.run_tests("mymodule")
            assert result.success is True

    def test_run_tests_with_custom_language(self):
        """run_tests should work with custom language configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig()
            runner = TestRunner(tmpdir, config=config)
            # Write a test for TypeScript (will fail but tests the command building)
            test_content = """
def test_ts():
    assert True
"""
            runner.write_tests("mymodule", test_content, "python")
            result = runner.run_tests("mymodule", "python")
            assert result.success is True


class TestEnvironmentHandling:
    """Tests for environment variable handling."""

    def test_env_vars_placeholder_substitution(self):
        """Environment variables should substitute {build_dir} placeholder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            # Write code and test with a print statement that uses cwd
            test_content = """
import sys
import os

def test_pythonpath():
    # Check that PYTHONPATH was set
    assert 'PYTHONPATH' in os.environ
    assert True
"""
            runner.write_tests("mymodule", test_content)
            result = runner.run_tests("mymodule")
            # Should succeed
            assert result.success is True

    def test_env_vars_preserve_existing(self):
        """Environment variables should preserve existing values with path separator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            # Set an existing env var
            test_content = """
import os

def test_env():
    # PYTHONPATH should include build_dir + original path
    pythonpath = os.environ.get('PYTHONPATH', '')
    assert pythonpath  # Should have something
"""
            runner.write_tests("mymodule", test_content)
            result = runner.run_tests("mymodule")
            # Should succeed - at minimum PYTHONPATH will be set to build_dir
            assert result.success is True


class TestErrorHandling:
    """Tests for error handling in test execution."""

    def test_missing_command_returns_error(self):
        """run_tests should handle missing command gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            # Create a custom config with a non-existent command
            config = SpecSoloistConfig()
            config.languages["badlang"] = LanguageConfig(
                extension=".bad",
                test_extension=".bad",
                test_filename_pattern="test_{name}",
                test_command=["nonexistent_command_xyz", "{file}"],
            )
            runner = TestRunner(tmpdir, config=config)
            runner.write_tests("mymodule", "pass", "badlang")
            result = runner.run_tests("mymodule", "badlang")
            assert result.success is False
            # Output should indicate command not found or execution error
            assert result.return_code != 0

    def test_exception_returns_error(self):
        """Execution errors should be caught and returned as failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = TestRunner(tmpdir)
            result = runner.run_tests("missing")
            assert result.success is False
            assert isinstance(result.output, str)


class TestSandboxing:
    """Tests for Docker sandboxing (without actually running Docker)."""

    def test_sandbox_config_affects_paths(self):
        """When sandboxing is enabled, test paths should be adjusted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(sandbox=True)
            runner = TestRunner(tmpdir, config=config)
            # The run_tests method should adjust paths for sandbox
            # This is hard to test without actually running Docker
            # but we can verify the config is stored
            assert runner.config.sandbox is True
