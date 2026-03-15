"""
Tests for sp vibe — single-command compose-then-conduct pipeline (task 19).
"""

import os
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from specsoloist.core import SpecSoloistCore
import specsoloist.cli as cli_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_core(tmp_path):
    """Create a minimal SpecSoloistCore pointing at tmp_path."""
    return SpecSoloistCore(str(tmp_path))


# ---------------------------------------------------------------------------
# cmd_vibe unit tests
# ---------------------------------------------------------------------------

class TestCmdVibe:
    """Unit tests for cmd_vibe — mocking compose and conduct."""

    def _call_vibe(self, core, brief, **kwargs):
        defaults = dict(
            template=None,
            pause_for_review=False,
            resume=False,
            no_agent=True,
            auto_accept=True,
            model=None,
        )
        defaults.update(kwargs)
        cli_module.cmd_vibe(core, brief, **defaults)

    def test_vibe_with_string_brief_calls_compose_then_conduct(self, tmp_path):
        core = make_core(tmp_path)
        with patch.object(cli_module, "cmd_compose") as mock_compose, \
             patch.object(cli_module, "cmd_conduct") as mock_conduct:
            self._call_vibe(core, "Build a todo app")
            assert mock_compose.called
            assert mock_conduct.called
            # compose called before conduct
            assert mock_compose.call_args_list[0][0][1] == "Build a todo app"

    def test_vibe_with_md_file_brief_reads_file(self, tmp_path):
        brief_file = tmp_path / "brief.md"
        brief_file.write_text("# Build a todo app\n\nWith auth and persistence.")
        core = make_core(tmp_path)
        with patch.object(cli_module, "cmd_compose") as mock_compose, \
             patch.object(cli_module, "cmd_conduct"):
            self._call_vibe(core, str(brief_file))
            # The request passed to compose should be the file content
            request_arg = mock_compose.call_args[0][1]
            assert "todo app" in request_arg.lower()

    def test_vibe_with_nonexistent_md_file_uses_as_string(self, tmp_path):
        """A .md path that doesn't exist is used as a string brief."""
        core = make_core(tmp_path)
        with patch.object(cli_module, "cmd_compose") as mock_compose, \
             patch.object(cli_module, "cmd_conduct"):
            self._call_vibe(core, "my_brief.md")
            request_arg = mock_compose.call_args[0][1]
            assert request_arg == "my_brief.md"

    def test_vibe_resume_flag_passes_to_conduct(self, tmp_path):
        core = make_core(tmp_path)
        with patch.object(cli_module, "cmd_compose"), \
             patch.object(cli_module, "cmd_conduct") as mock_conduct:
            self._call_vibe(core, "Build something", resume=True)
            conduct_kwargs = mock_conduct.call_args[1]
            assert conduct_kwargs.get("resume") is True

    def test_vibe_resume_false_by_default(self, tmp_path):
        core = make_core(tmp_path)
        with patch.object(cli_module, "cmd_compose"), \
             patch.object(cli_module, "cmd_conduct") as mock_conduct:
            self._call_vibe(core, "Build something", resume=False)
            conduct_kwargs = mock_conduct.call_args[1]
            assert conduct_kwargs.get("resume") is False

    def test_vibe_model_passes_to_both_compose_and_conduct(self, tmp_path):
        core = make_core(tmp_path)
        with patch.object(cli_module, "cmd_compose") as mock_compose, \
             patch.object(cli_module, "cmd_conduct") as mock_conduct:
            self._call_vibe(core, "Build something", model="claude-haiku")
            # compose receives model
            compose_kwargs = mock_compose.call_args[1]
            assert compose_kwargs.get("model") == "claude-haiku"
            # conduct receives model
            conduct_kwargs = mock_conduct.call_args[1]
            assert conduct_kwargs.get("model") == "claude-haiku"

    def test_vibe_no_brief_exits_with_error(self, tmp_path):
        core = make_core(tmp_path)
        with pytest.raises(SystemExit) as exc_info:
            self._call_vibe(core, None)
        assert exc_info.value.code == 1

    def test_vibe_pause_for_review_calls_input(self, tmp_path):
        core = make_core(tmp_path)
        with patch.object(cli_module, "cmd_compose"), \
             patch.object(cli_module, "cmd_conduct"), \
             patch("builtins.input", return_value="") as mock_input:
            self._call_vibe(core, "Build something", pause_for_review=True)
            assert mock_input.called

    def test_vibe_no_pause_by_default_does_not_call_input(self, tmp_path):
        core = make_core(tmp_path)
        with patch.object(cli_module, "cmd_compose"), \
             patch.object(cli_module, "cmd_conduct"), \
             patch("builtins.input") as mock_input:
            self._call_vibe(core, "Build something", pause_for_review=False)
            assert not mock_input.called


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

class TestVibeHelp:
    def test_vibe_help_output(self):
        """sp vibe --help should document the command."""
        import subprocess
        result = subprocess.run(
            ["uv", "run", "sp", "vibe", "--help"],
            capture_output=True, text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert "brief" in result.stdout.lower()
        assert "--pause-for-review" in result.stdout
        assert "--resume" in result.stdout
        assert "--model" in result.stdout

    def test_vibe_appears_in_sp_help(self):
        """sp --help should list 'vibe' as a command."""
        import subprocess
        result = subprocess.run(
            ["uv", "run", "sp", "--help"],
            capture_output=True, text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert "vibe" in result.stdout
