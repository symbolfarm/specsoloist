"""Tests for arrangement env_vars field: parsing, prompt injection, doctor check."""

import os
import tempfile

import pytest
import yaml

from specsoloist.compiler import SpecCompiler
from specsoloist.parser import SpecParser
from specsoloist.schema import (
    Arrangement,
    ArrangementBuildCommands,
    ArrangementEnvVar,
    ArrangementOutputPaths,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal Arrangement with env_vars
# ---------------------------------------------------------------------------


def _make_arrangement(env_vars: dict | None = None) -> Arrangement:
    return Arrangement(
        target_language="python",
        output_paths=ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py",
        ),
        build_commands=ArrangementBuildCommands(test="pytest"),
        env_vars=env_vars or {},
    )


# ---------------------------------------------------------------------------
# 1. Schema: parsing env_vars from YAML
# ---------------------------------------------------------------------------


def test_env_vars_parsed_from_yaml():
    """Arrangement.env_vars is populated when the YAML declares env_vars."""
    raw = {
        "target_language": "typescript",
        "output_paths": {"implementation": "src/{name}.ts", "tests": "tests/{name}.test.ts"},
        "build_commands": {"test": "npx vitest run"},
        "env_vars": {
            "OPENAI_API_KEY": {
                "description": "OpenAI API key",
                "required": True,
                "example": "sk-...",
            },
            "DATABASE_URL": {
                "description": "SQLite connection string",
                "required": False,
                "example": "sqlite:///./todos.db",
            },
        },
    }
    arr = Arrangement(**raw)

    assert "OPENAI_API_KEY" in arr.env_vars
    assert arr.env_vars["OPENAI_API_KEY"].required is True
    assert arr.env_vars["OPENAI_API_KEY"].example == "sk-..."

    assert "DATABASE_URL" in arr.env_vars
    assert arr.env_vars["DATABASE_URL"].required is False


def test_env_vars_defaults_to_empty():
    """Arrangement without env_vars key parses without error, defaults to {}."""
    raw = {
        "target_language": "python",
        "output_paths": {"implementation": "src/{name}.py", "tests": "tests/test_{name}.py"},
        "build_commands": {"test": "pytest"},
    }
    arr = Arrangement(**raw)
    assert arr.env_vars == {}


def test_arrangement_env_var_required_default():
    """ArrangementEnvVar.required defaults to True."""
    var = ArrangementEnvVar(description="Some key")
    assert var.required is True
    assert var.example == ""


# ---------------------------------------------------------------------------
# 2. Compiler: env_vars injected into prompt
# ---------------------------------------------------------------------------


def test_compiler_injects_env_vars_into_prompt():
    """When env_vars are declared, the arrangement context includes an Environment Variables section."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        parser = SpecParser(tmp_dir)
        compiler = SpecCompiler(parser)

        arr = _make_arrangement(
            env_vars={
                "OPENAI_API_KEY": ArrangementEnvVar(
                    description="OpenAI API key",
                    required=True,
                    example="sk-...",
                ),
                "DATABASE_URL": ArrangementEnvVar(
                    description="SQLite connection string",
                    required=False,
                    example="sqlite:///./todos.db",
                ),
            }
        )

        context = compiler._build_arrangement_context(arr)

        assert "Environment Variables" in context
        assert "OPENAI_API_KEY" in context
        assert "required" in context
        assert "DATABASE_URL" in context
        assert "optional" in context


def test_compiler_omits_env_vars_section_when_empty():
    """When env_vars is empty, the arrangement context does NOT include an Environment Variables section."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        parser = SpecParser(tmp_dir)
        compiler = SpecCompiler(parser)

        arr = _make_arrangement(env_vars={})  # no env vars
        context = compiler._build_arrangement_context(arr)

        assert "Environment Variables" not in context


# ---------------------------------------------------------------------------
# 3. sp doctor: warns about unset required env vars
# ---------------------------------------------------------------------------


def test_doctor_detects_unset_required_env_var(tmp_path, monkeypatch, capsys):
    """cmd_doctor reports an error for an unset required env var in arrangement."""
    from specsoloist.cli import cmd_doctor

    arrangement_data = {
        "target_language": "python",
        "output_paths": {"implementation": "src/{name}.py", "tests": "tests/test_{name}.py"},
        "build_commands": {"test": "pytest"},
        "env_vars": {
            "MY_REQUIRED_API_KEY": {
                "description": "A required API key for testing",
                "required": True,
            },
        },
    }
    arr_file = tmp_path / "arrangement.yaml"
    arr_file.write_text(yaml.dump(arrangement_data))

    # Ensure the key is NOT set in the environment
    monkeypatch.delenv("MY_REQUIRED_API_KEY", raising=False)
    # Also set at least one real API key so doctor doesn't fail on that
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    import sys
    with pytest.raises(SystemExit) as exc_info:
        cmd_doctor(arrangement_arg=str(arr_file))

    # Should exit non-zero because required var is missing
    assert exc_info.value.code != 0


def test_doctor_passes_when_required_env_var_set(tmp_path, monkeypatch):
    """cmd_doctor passes when all required env vars are set."""
    from specsoloist.cli import cmd_doctor

    arrangement_data = {
        "target_language": "python",
        "output_paths": {"implementation": "src/{name}.py", "tests": "tests/test_{name}.py"},
        "build_commands": {"test": "pytest"},
        "env_vars": {
            "MY_REQUIRED_API_KEY": {
                "description": "A required API key for testing",
                "required": True,
            },
        },
    }
    arr_file = tmp_path / "arrangement.yaml"
    arr_file.write_text(yaml.dump(arrangement_data))

    monkeypatch.setenv("MY_REQUIRED_API_KEY", "test-value")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    # Should NOT raise SystemExit
    try:
        cmd_doctor(arrangement_arg=str(arr_file))
    except SystemExit as e:
        pytest.fail(f"cmd_doctor raised SystemExit({e.code}) unexpectedly")


def test_doctor_optional_env_var_not_set_is_ok(tmp_path, monkeypatch):
    """cmd_doctor does not fail when an optional env var is unset."""
    from specsoloist.cli import cmd_doctor

    arrangement_data = {
        "target_language": "python",
        "output_paths": {"implementation": "src/{name}.py", "tests": "tests/test_{name}.py"},
        "build_commands": {"test": "pytest"},
        "env_vars": {
            "OPTIONAL_KEY": {
                "description": "Optional configuration",
                "required": False,
                "example": "default-value",
            },
        },
    }
    arr_file = tmp_path / "arrangement.yaml"
    arr_file.write_text(yaml.dump(arrangement_data))

    monkeypatch.delenv("OPTIONAL_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    # Should NOT raise SystemExit (optional var being unset is not an error)
    try:
        cmd_doctor(arrangement_arg=str(arr_file))
    except SystemExit as e:
        pytest.fail(f"cmd_doctor raised SystemExit({e.code}) for unset optional var")
