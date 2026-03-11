"""Tests for _run_agent_oneshot() permission flag scoping."""

from unittest.mock import patch, MagicMock

from specsoloist.cli import _run_agent_oneshot


def _run(agent, auto_accept, model=None):
    """Helper: capture the cmd passed to subprocess.run."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        _run_agent_oneshot(agent, "test prompt", auto_accept, model=model)
        return mock_run.call_args[0][0]  # the cmd list


class TestClaudePermissions:
    def test_no_auto_accept_no_permission_flags(self):
        cmd = _run("claude", auto_accept=False)
        assert "--permission-mode" not in cmd
        assert "--dangerously-skip-permissions" not in cmd

    def test_auto_accept_uses_dangerously_skip(self):
        cmd = _run("claude", auto_accept=True)
        assert "--dangerously-skip-permissions" in cmd
        assert "bypassPermissions" not in cmd


class TestGeminiPermissions:
    def test_no_auto_accept(self):
        cmd = _run("gemini", auto_accept=False)
        assert "-y" not in cmd

    def test_auto_accept(self):
        cmd = _run("gemini", auto_accept=True)
        assert "-y" in cmd
