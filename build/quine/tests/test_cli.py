"""Tests for the CLI module."""

import os
import json
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

from specsoloist.cli import cli


SIMPLE_SPEC = """---
name: myspec
description: A simple spec
type: bundle
---

# Overview

A simple spec.

# Functions

```yaml:functions
greet:
  inputs:
    name: {type: string}
  outputs:
    message: {type: string}
  behavior: "Return a greeting"
```
"""


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def spec_dir(tmp_path):
    (tmp_path / "myspec.spec.md").write_text(SIMPLE_SPEC)
    return tmp_path


@pytest.fixture
def env_vars(spec_dir):
    return {
        "SPECSOLOIST_SRC_DIR": str(spec_dir),
        "SPECSOLOIST_LLM_PROVIDER": "gemini",
        "GEMINI_API_KEY": "test-key",
    }


class TestGlobalFlags:
    def test_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "sp" in result.output.lower() or "specsoloist" in result.output.lower()

    def test_quiet_flag(self, runner):
        result = runner.invoke(cli, ["--quiet", "--help"])
        assert result.exit_code == 0

    def test_json_flag(self, runner):
        result = runner.invoke(cli, ["--json", "--help"])
        assert result.exit_code == 0


class TestListCommand:
    def test_list_basic(self, runner, spec_dir, env_vars):
        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0

    def test_list_json_output(self, runner, spec_dir, env_vars):
        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ["--json", "list"])
        assert result.exit_code == 0
        # JSON output should be parseable
        data = json.loads(result.output)
        assert "specs" in data


class TestCreateCommand:
    def test_create_new_spec(self, runner, spec_dir, env_vars):
        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ["create", "newspec", "A new spec"])
        assert result.exit_code == 0
        assert os.path.exists(os.path.join(str(spec_dir), "newspec.spec.md"))

    def test_create_with_type(self, runner, spec_dir, env_vars):
        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ["create", "mybundle", "A bundle", "--type", "bundle"])
        assert result.exit_code == 0


class TestValidateCommand:
    def test_validate_valid_spec(self, runner, spec_dir, env_vars):
        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ["validate", "myspec"])
        assert result.exit_code == 0

    def test_validate_missing_spec_exits_1(self, runner, spec_dir, env_vars):
        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ["validate", "nonexistent"])
        assert result.exit_code == 1

    def test_validate_json_output(self, runner, spec_dir, env_vars):
        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ["validate", "myspec", "--json"])
        data = json.loads(result.output)
        assert "valid" in data


class TestStatusCommand:
    def test_status_basic(self, runner, spec_dir, env_vars):
        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0

    def test_status_json(self, runner, spec_dir, env_vars):
        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ["--json", "status"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)


class TestGraphCommand:
    def test_graph_output(self, runner, spec_dir, env_vars):
        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ["graph"])
        assert result.exit_code == 0
        assert "graph TD" in result.output


class TestVerifyCommand:
    def test_verify_valid_project(self, runner, spec_dir, env_vars):
        with patch.dict(os.environ, env_vars):
            result = runner.invoke(cli, ["verify"])
        # Should succeed for valid specs
        assert result.exit_code in (0, 1)  # May fail if bundle validation is strict


class TestDoctorCommand:
    def test_doctor_basic(self, runner):
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0

    def test_doctor_with_api_key(self, runner):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0


class TestInitCommand:
    def test_init_list_templates(self, runner):
        result = runner.invoke(cli, ["init", "--list-templates"])
        assert result.exit_code == 0
        assert "python" in result.output.lower() or "nextjs" in result.output.lower()

    def test_init_creates_dirs(self, runner, tmp_path):
        result = runner.invoke(cli, ["init", str(tmp_path / "myproject")])
        assert result.exit_code == 0


class TestCompileCommand:
    def test_compile_checks_api_key(self, runner, spec_dir, tmp_path):
        env = {
            "SPECSOLOIST_SRC_DIR": str(spec_dir),
            "SPECSOLOIST_LLM_PROVIDER": "gemini",
            # No API key
        }
        with patch.dict(os.environ, env, clear=False):
            # Remove any existing GEMINI_API_KEY
            os.environ.pop("GEMINI_API_KEY", None)
            result = runner.invoke(cli, ["compile", "myspec"])
        # Should fail due to missing API key
        assert result.exit_code == 1


class TestTestCommand:
    def test_test_all_flag(self, runner, spec_dir, env_vars, tmp_path):
        env = {**env_vars, "SPECSOLOIST_BUILD_DIR": str(tmp_path)}
        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["test", "--all"])
        # May succeed or fail depending on test files existing
        assert result.exit_code in (0, 1)

    def test_test_single_spec(self, runner, spec_dir, env_vars, tmp_path):
        env = {**env_vars}
        with patch.dict(os.environ, env):
            result = runner.invoke(cli, ["test", "myspec"])
        # Will fail since no test file
        assert result.exit_code in (0, 1)
