"""
Tests for model pinning in arrangement files (task 17).
"""

import os
import textwrap

import pytest
import yaml

from specsoloist.schema import Arrangement


def make_arrangement(model=None, extra=None):
    """Build a minimal Arrangement dict, optionally with a model field."""
    data = {
        "target_language": "python",
        "output_paths": {
            "implementation": "src/{name}.py",
            "tests": "tests/test_{name}.py",
        },
        "build_commands": {
            "test": "uv run pytest",
        },
    }
    if model is not None:
        data["model"] = model
    if extra:
        data.update(extra)
    return data


# ---------------------------------------------------------------------------
# Schema: Arrangement.model field
# ---------------------------------------------------------------------------

class TestArrangementModelField:
    def test_arrangement_without_model_parses(self):
        arr = Arrangement(**make_arrangement())
        assert arr.model is None

    def test_arrangement_with_model_parses(self):
        arr = Arrangement(**make_arrangement(model="claude-haiku-4-5-20251001"))
        assert arr.model == "claude-haiku-4-5-20251001"

    def test_arrangement_model_none_by_default(self):
        arr = Arrangement(**make_arrangement())
        assert arr.model is None

    def test_arrangement_model_preserves_value(self):
        arr = Arrangement(**make_arrangement(model="gemini-2.0-flash"))
        assert arr.model == "gemini-2.0-flash"

    def test_arrangement_from_yaml_with_model(self, tmp_path):
        """Arrangement loaded from a YAML file includes the model field."""
        arr_data = make_arrangement(model="claude-3-haiku-20240307")
        arr_file = tmp_path / "arrangement.yaml"
        arr_file.write_text(yaml.dump(arr_data))

        with open(arr_file) as f:
            loaded = yaml.safe_load(f)
        arr = Arrangement(**loaded)
        assert arr.model == "claude-3-haiku-20240307"

    def test_arrangement_from_yaml_without_model(self, tmp_path):
        """Arrangement loaded from YAML without model field has model=None."""
        arr_data = make_arrangement()  # no model
        arr_file = tmp_path / "arrangement.yaml"
        arr_file.write_text(yaml.dump(arr_data))

        with open(arr_file) as f:
            loaded = yaml.safe_load(f)
        arr = Arrangement(**loaded)
        assert arr.model is None


# ---------------------------------------------------------------------------
# _resolve_model precedence
# ---------------------------------------------------------------------------

class TestResolveModel:
    """Test the CLI _resolve_model helper directly."""

    def _get_resolve_model(self):
        from specsoloist.cli import _resolve_model
        return _resolve_model

    def test_cli_flag_wins_over_arrangement(self):
        _resolve_model = self._get_resolve_model()
        arr = Arrangement(**make_arrangement(model="arrangement-model"))
        result = _resolve_model("cli-model", arr)
        assert result == "cli-model"

    def test_arrangement_model_used_when_no_cli_flag(self):
        _resolve_model = self._get_resolve_model()
        arr = Arrangement(**make_arrangement(model="arrangement-model"))
        result = _resolve_model(None, arr)
        assert result == "arrangement-model"

    def test_none_returned_when_neither_set(self):
        _resolve_model = self._get_resolve_model()
        arr = Arrangement(**make_arrangement())  # no model
        result = _resolve_model(None, arr)
        assert result is None

    def test_none_returned_when_no_arrangement(self):
        _resolve_model = self._get_resolve_model()
        result = _resolve_model(None, None)
        assert result is None

    def test_cli_flag_wins_over_arrangement_and_env(self, monkeypatch):
        _resolve_model = self._get_resolve_model()
        monkeypatch.setenv("SPECSOLOIST_LLM_MODEL", "env-model")
        arr = Arrangement(**make_arrangement(model="arrangement-model"))
        result = _resolve_model("cli-model", arr)
        assert result == "cli-model"

    def test_empty_string_cli_model_falls_through_to_arrangement(self):
        """An empty string for cli_model is falsy — arrangement should win."""
        _resolve_model = self._get_resolve_model()
        arr = Arrangement(**make_arrangement(model="arrangement-model"))
        result = _resolve_model("", arr)
        assert result == "arrangement-model"
