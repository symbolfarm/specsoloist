"""Tests for nested Claude Code session detection and warning."""

import os
from unittest.mock import patch, MagicMock

import pytest

from specsoloist.cli import _detect_nested_session, _run_agent_oneshot


# ---------------------------------------------------------------------------
# Detection logic
# ---------------------------------------------------------------------------


def test_detect_nested_session_claude_via_claudecode_var(monkeypatch):
    """CLAUDECODE env var triggers nested session detection for claude agent."""
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.delenv("CLAUDE_CODE_ENTRYPOINT", raising=False)
    assert _detect_nested_session("claude") is True


def test_detect_nested_session_claude_via_entrypoint_var(monkeypatch):
    """CLAUDE_CODE_ENTRYPOINT env var triggers nested session detection for claude agent."""
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "/usr/bin/claude")
    assert _detect_nested_session("claude") is True


def test_detect_nested_session_not_claude_when_vars_absent(monkeypatch):
    """No nested session detected for claude when neither env var is set."""
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_ENTRYPOINT", raising=False)
    # Also ensure psutil (if present) doesn't fire
    with patch("specsoloist.cli.psutil", None, create=True):
        # Patch the try/except path in _detect_nested_session
        with patch("builtins.__import__", side_effect=ImportError):
            pass  # psutil import will just fail gracefully
        result = _detect_nested_session("claude")
    # Without env vars (and no psutil parent process match), should be False
    assert result is False


def test_detect_nested_session_gemini_via_var(monkeypatch):
    """GEMINI_CLI_SESSION env var triggers nested session detection for gemini agent."""
    monkeypatch.setenv("GEMINI_CLI_SESSION", "1")
    assert _detect_nested_session("gemini") is True


def test_detect_nested_session_gemini_not_detected_without_var(monkeypatch):
    """No nested session detected for gemini without the env var set."""
    monkeypatch.delenv("GEMINI_CLI_SESSION", raising=False)
    monkeypatch.delenv("GEMINI_TERMINAL", raising=False)
    result = _detect_nested_session("gemini")
    # Without vars (and no psutil match), should be False
    assert result is False


# ---------------------------------------------------------------------------
# Warning is shown when nested session detected
# ---------------------------------------------------------------------------


def test_run_agent_oneshot_shows_warning_when_nested(monkeypatch):
    """_run_agent_oneshot prints a warning panel when inside a nested session."""
    monkeypatch.setenv("CLAUDECODE", "1")

    mock_result = MagicMock()
    mock_result.returncode = 0

    from rich.panel import Panel

    printed_objects = []

    def fake_print_capture(obj, *args, **kwargs):
        printed_objects.append(obj)

    with patch("subprocess.run", return_value=mock_result):
        with patch("specsoloist.cli.ui.console.print", side_effect=fake_print_capture):
            _run_agent_oneshot("claude", "test prompt", auto_accept=False)

    # At least one Panel should have been printed (the warning panel)
    assert any(isinstance(obj, Panel) for obj in printed_objects), \
        f"Expected a Rich Panel warning in output, got: {printed_objects}"


def test_run_agent_oneshot_no_warning_outside_session(monkeypatch):
    """_run_agent_oneshot does NOT print a warning when not in a nested session."""
    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_ENTRYPOINT", raising=False)

    mock_result = MagicMock()
    mock_result.returncode = 0

    printed_text = []

    def fake_print(obj, *args, **kwargs):
        printed_text.append(str(obj))

    with patch("subprocess.run", return_value=mock_result):
        with patch("specsoloist.cli.ui.console.print", side_effect=fake_print):
            _run_agent_oneshot("claude", "test prompt", auto_accept=False)

    # No warning panel for a non-nested session
    assert not any("Heads Up" in t for t in printed_text), \
        f"Unexpected nested session warning: {printed_text}"


# ---------------------------------------------------------------------------
# Friendly error message on failure when nested
# ---------------------------------------------------------------------------


def test_run_agent_oneshot_friendly_error_on_failure_when_nested(monkeypatch):
    """When nested and subprocess fails, error message is actionable."""
    monkeypatch.setenv("CLAUDECODE", "1")

    mock_result = MagicMock()
    mock_result.returncode = 1

    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError) as exc_info:
            _run_agent_oneshot("claude", "test prompt", auto_accept=False)

    error_msg = str(exc_info.value)
    assert "conductor agent failed" in error_msg.lower() or "claude code" in error_msg.lower() or \
           "--no-agent" in error_msg
