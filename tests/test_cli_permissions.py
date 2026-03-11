"""Tests for _run_agent_oneshot() permission flag scoping."""

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from specsoloist.cli import _run_agent_oneshot


def _run(agent, auto_accept, is_quine=False, model=None):
    """Helper: capture the cmd passed to subprocess.run."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        _run_agent_oneshot(agent, "test prompt", auto_accept, model=model, is_quine=is_quine)
        return mock_run.call_args[0][0]  # the cmd list


class TestClaudePermissions:
    def test_no_auto_accept_no_permission_flags(self):
        cmd = _run("claude", auto_accept=False)
        assert "--permission-mode" not in cmd
        assert "--dangerously-skip-permissions" not in cmd

    def test_auto_accept_non_quine_uses_dangerously_skip(self):
        cmd = _run("claude", auto_accept=True, is_quine=False)
        assert "--dangerously-skip-permissions" in cmd
        assert "bypassPermissions" not in cmd

    def test_auto_accept_quine_uses_bypass_permissions(self):
        cmd = _run("claude", auto_accept=True, is_quine=True)
        assert "--permission-mode" in cmd
        assert cmd[cmd.index("--permission-mode") + 1] == "bypassPermissions"
        assert "--dangerously-skip-permissions" not in cmd

    def test_is_quine_without_auto_accept_no_permission_flags(self):
        cmd = _run("claude", auto_accept=False, is_quine=True)
        assert "--permission-mode" not in cmd
        assert "--dangerously-skip-permissions" not in cmd


class TestGeminiPermissions:
    def test_no_auto_accept(self):
        cmd = _run("gemini", auto_accept=False)
        assert "-y" not in cmd

    def test_auto_accept(self):
        cmd = _run("gemini", auto_accept=True)
        assert "-y" in cmd

    def test_auto_accept_quine(self):
        # Gemini always uses -y; is_quine doesn't affect it
        cmd = _run("gemini", auto_accept=True, is_quine=True)
        assert "-y" in cmd
