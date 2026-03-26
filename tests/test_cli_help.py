"""Tests for sp help command (task 23)."""

import os
import subprocess
import sys

import pytest


def run_sp(*args, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "specsoloist.cli", *args],
        capture_output=True,
        text=True,
        cwd=cwd or os.getcwd(),
    )


@pytest.fixture()
def tmp_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestSpHelp:
    def test_help_no_topic_exits_0(self, tmp_cwd):
        result = run_sp("help")
        assert result.returncode == 0

    def test_help_lists_arrangement(self, tmp_cwd):
        result = run_sp("help")
        combined = result.stdout + result.stderr
        assert "arrangement" in combined

    def test_help_lists_spec_format(self, tmp_cwd):
        result = run_sp("help")
        combined = result.stdout + result.stderr
        assert "spec-format" in combined

    def test_help_lists_conduct(self, tmp_cwd):
        result = run_sp("help")
        combined = result.stdout + result.stderr
        assert "conduct" in combined

    def test_help_arrangement_exits_0(self, tmp_cwd):
        result = run_sp("help", "arrangement")
        assert result.returncode == 0

    def test_help_arrangement_contains_output_paths(self, tmp_cwd):
        result = run_sp("help", "arrangement")
        assert "output_paths" in result.stdout

    def test_help_arrangement_contains_overrides(self, tmp_cwd):
        result = run_sp("help", "arrangement")
        assert "overrides" in result.stdout

    def test_help_arrangement_contains_specs_path(self, tmp_cwd):
        result = run_sp("help", "arrangement")
        assert "specs_path" in result.stdout

    def test_help_spec_format_exits_0(self, tmp_cwd):
        result = run_sp("help", "spec-format")
        assert result.returncode == 0

    def test_help_conduct_exits_0(self, tmp_cwd):
        result = run_sp("help", "conduct")
        assert result.returncode == 0

    def test_help_overrides_exits_0(self, tmp_cwd):
        result = run_sp("help", "overrides")
        assert result.returncode == 0

    def test_help_specs_path_exits_0(self, tmp_cwd):
        result = run_sp("help", "specs-path")
        assert result.returncode == 0

    def test_help_bogus_topic_exits_nonzero(self, tmp_cwd):
        result = run_sp("help", "bogus")
        assert result.returncode != 0

    def test_help_bogus_topic_shows_available(self, tmp_cwd):
        result = run_sp("help", "bogus")
        combined = result.stdout + result.stderr
        assert "arrangement" in combined

    def test_help_works_without_project_context(self, tmp_path):
        """sp help must work from an empty directory."""
        result = run_sp("help", "arrangement", cwd=str(tmp_path))
        assert result.returncode == 0

    def test_read_help_file_returns_content(self):
        """_read_help_file returns non-empty string for bundled topics."""
        from specsoloist.cli import _read_help_file
        content = _read_help_file("arrangement")
        assert content is not None
        assert len(content) > 100

    def test_read_help_file_returns_none_for_unknown(self):
        from specsoloist.cli import _read_help_file
        assert _read_help_file("nonexistent_topic") is None
