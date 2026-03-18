"""Tests for the runner module."""

import os
import pytest
from unittest.mock import patch, MagicMock

from specsoloist.config import SpecSoloistConfig
from specsoloist.runner import TestResult, TestRunner


@pytest.fixture
def runner(tmp_path):
    config = SpecSoloistConfig()
    return TestRunner(build_dir=str(tmp_path), config=config)


class TestTestResult:
    def test_success_result(self):
        result = TestResult(success=True, output="All tests passed", return_code=0)
        assert result.success is True
        assert result.return_code == 0

    def test_failure_result(self):
        result = TestResult(success=False, output="1 failed", return_code=1)
        assert result.success is False


class TestTestRunnerPaths:
    def test_get_code_path_python(self, runner, tmp_path):
        path = runner.get_code_path("mymodule")
        assert path == os.path.join(str(tmp_path), "mymodule.py")

    def test_get_code_path_typescript(self, runner, tmp_path):
        path = runner.get_code_path("mymodule", language="typescript")
        assert path == os.path.join(str(tmp_path), "mymodule.ts")

    def test_get_test_path_python(self, runner, tmp_path):
        path = runner.get_test_path("mymodule")
        assert "test_mymodule" in path
        assert path.endswith(".py")

    def test_get_test_path_typescript(self, runner, tmp_path):
        path = runner.get_test_path("mymodule", language="typescript")
        assert "mymodule.test" in path
        assert path.endswith(".ts")


class TestTestRunnerFileOps:
    def test_write_and_read_code(self, runner):
        runner.write_code("mymodule", "def foo(): pass")
        assert runner.code_exists("mymodule")
        content = runner.read_code("mymodule")
        assert content == "def foo(): pass"

    def test_write_and_read_tests(self, runner):
        runner.write_tests("mymodule", "def test_foo(): pass")
        assert runner.test_exists("mymodule")
        content = runner.read_tests("mymodule")
        assert content == "def test_foo(): pass"

    def test_code_not_exists_initially(self, runner):
        assert runner.code_exists("nonexistent") is False

    def test_test_not_exists_initially(self, runner):
        assert runner.test_exists("nonexistent") is False

    def test_read_code_missing_returns_none(self, runner):
        assert runner.read_code("nonexistent") is None

    def test_read_tests_missing_returns_none(self, runner):
        assert runner.read_tests("nonexistent") is None

    def test_write_file_uses_basename(self, runner, tmp_path):
        path = runner.write_file("some/path/myfile.txt", "content")
        # Should only use basename
        assert os.path.dirname(path) == str(tmp_path)
        assert os.path.basename(path) == "myfile.txt"
        assert open(path).read() == "content"


class TestTestRunnerExecution:
    def test_run_tests_no_test_file_fails(self, runner):
        result = runner.run_tests("nonexistent_module")
        assert result.success is False
        assert "not found" in result.output.lower() or result.return_code != 0

    def test_run_tests_success(self, runner, tmp_path):
        # Write a simple passing test
        test_content = "def test_simple(): assert 1 + 1 == 2\n"
        runner.write_tests("simple", test_content)
        test_path = runner.get_test_path("simple")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="1 passed", stderr="")
            result = runner.run_tests("simple")
            assert result.success is True

    def test_run_tests_failure(self, runner):
        # Write a failing test
        runner.write_tests("failing", "def test_fail(): assert False\n")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="1 failed", stderr="")
            result = runner.run_tests("failing")
            assert result.success is False

    def test_run_tests_handles_command_not_found(self, runner):
        runner.write_tests("mymod", "def test_foo(): pass\n")

        with patch("subprocess.run", side_effect=FileNotFoundError("python not found")):
            result = runner.run_tests("mymod")
            assert result.success is False
            assert result.return_code != 0

    def test_run_tests_sets_env_vars(self, runner, tmp_path):
        runner.write_tests("mymod", "def test_foo(): pass\n")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            runner.run_tests("mymod")
            # Check that PYTHONPATH was set in the env
            call_kwargs = mock_run.call_args
            if call_kwargs:
                env = call_kwargs[1].get("env", {})
                # env should have PYTHONPATH set
                assert "PYTHONPATH" in env

    def test_run_tests_combines_stdout_stderr(self, runner):
        runner.write_tests("mymod", "def test_foo(): pass\n")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="stdout content", stderr="stderr content"
            )
            result = runner.run_tests("mymod")
            assert "stdout content" in result.output
            assert "stderr content" in result.output


class TestSandboxExecution:
    def test_sandbox_wraps_in_docker(self, tmp_path):
        config = SpecSoloistConfig(sandbox=True, sandbox_image="my-sandbox")
        runner = TestRunner(build_dir=str(tmp_path), config=config)
        runner.write_tests("mymod", "def test_foo(): pass\n")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            runner.run_tests("mymod")
            cmd = mock_run.call_args[0][0]
            assert "docker" in cmd
            assert "run" in cmd
            assert "my-sandbox" in cmd
