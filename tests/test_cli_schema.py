"""Tests for sp schema command (task 22)."""

import json
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


class TestSpSchema:
    def test_schema_exits_0(self, tmp_cwd):
        result = run_sp("schema")
        assert result.returncode == 0

    def test_schema_contains_specs_path(self, tmp_cwd):
        result = run_sp("schema")
        assert "specs_path" in result.stdout

    def test_schema_contains_output_paths(self, tmp_cwd):
        result = run_sp("schema")
        assert "output_paths" in result.stdout

    def test_schema_output_paths_topic(self, tmp_cwd):
        result = run_sp("schema", "output_paths")
        assert result.returncode == 0
        assert "overrides" in result.stdout
        # specs_path is not part of output_paths — should not appear in topic output
        assert "specs_path" not in result.stdout

    def test_schema_topic_exits_0(self, tmp_cwd):
        result = run_sp("schema", "environment")
        assert result.returncode == 0
        assert "tools" in result.stdout

    def test_schema_json_is_valid_json(self, tmp_cwd):
        result = run_sp("schema", "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "type" in data or "$defs" in data or "properties" in data

    def test_schema_json_topic(self, tmp_cwd):
        result = run_sp("schema", "output_paths", "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "properties" in data or "type" in data

    def test_schema_bogus_topic_exits_nonzero(self, tmp_cwd):
        result = run_sp("schema", "nonexistent_field")
        assert result.returncode != 0

    def test_schema_bogus_topic_lists_valid(self, tmp_cwd):
        result = run_sp("schema", "nonexistent_field")
        combined = result.stdout + result.stderr
        assert "output_paths" in combined

    def test_schema_works_without_project_context(self, tmp_path):
        """sp schema must work from an empty directory with no arrangement.yaml."""
        result = run_sp("schema", cwd=str(tmp_path))
        assert result.returncode == 0
        assert "target_language" in result.stdout
