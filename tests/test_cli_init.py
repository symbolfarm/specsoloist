"""Tests for the `sp init` command."""

import subprocess
import sys
import pytest


@pytest.fixture()
def tmp_cwd(tmp_path, monkeypatch):
    """Run tests in a temporary directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run_init(name: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "specsoloist.cli", "init", name],
        capture_output=True,
        text=True,
    )


class TestSpInit:
    def test_creates_specs_dir(self, tmp_cwd):
        result = run_init("myproject")
        assert result.returncode == 0
        assert (tmp_cwd / "myproject" / "specs").is_dir()

    def test_creates_arrangement_yaml(self, tmp_cwd):
        run_init("myproject")
        arrangement = (tmp_cwd / "myproject" / "arrangement.yaml")
        assert arrangement.exists()
        content = arrangement.read_text()
        assert "target_language: python" in content
        assert "output_paths" in content

    def test_creates_gitignore(self, tmp_cwd):
        run_init("myproject")
        gitignore = (tmp_cwd / "myproject" / ".gitignore")
        assert gitignore.exists()
        content = gitignore.read_text()
        assert "__pycache__" in content
        assert "build/" in content
        assert "node_modules/" in content

    def test_fails_if_directory_exists(self, tmp_cwd):
        (tmp_cwd / "myproject").mkdir()
        result = run_init("myproject")
        assert result.returncode != 0
        assert "already exists" in result.stderr or "already exists" in result.stdout

    def test_nested_name_creates_correct_structure(self, tmp_cwd):
        run_init("foo")
        assert (tmp_cwd / "foo" / "specs").is_dir()
        assert (tmp_cwd / "foo" / "arrangement.yaml").exists()
        assert (tmp_cwd / "foo" / ".gitignore").exists()
