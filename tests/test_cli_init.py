"""Tests for the `sp init` command."""

import subprocess
import sys
import pytest


@pytest.fixture()
def tmp_cwd(tmp_path, monkeypatch):
    """Run tests in a temporary directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run_init(name: str, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "specsoloist.cli", "init", name, *extra_args],
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

    def test_typescript_arrangement(self, tmp_cwd):
        result = run_init("tsproject", "--arrangement", "typescript")
        assert result.returncode == 0
        content = (tmp_cwd / "tsproject" / "arrangement.yaml").read_text()
        assert "target_language: typescript" in content
        assert "vitest" in content
        assert "tsconfig.json" in content

    def test_python_is_default(self, tmp_cwd):
        run_init("pyproject")
        content = (tmp_cwd / "pyproject" / "arrangement.yaml").read_text()
        assert "target_language: python" in content

    def test_invalid_arrangement_rejected(self, tmp_cwd):
        result = run_init("bad", "--arrangement", "ruby")
        assert result.returncode != 0

    def test_arrangement_contains_specs_path_comment(self, tmp_cwd):
        """Generated arrangement.yaml includes a commented specs_path example (task 24)."""
        run_init("myproject")
        content = (tmp_cwd / "myproject" / "arrangement.yaml").read_text()
        assert "specs_path" in content

    def test_arrangement_contains_overrides_comment(self, tmp_cwd):
        """Generated arrangement.yaml includes a commented overrides example (task 24)."""
        run_init("myproject")
        content = (tmp_cwd / "myproject" / "arrangement.yaml").read_text()
        assert "overrides" in content

    def test_fasthtml_template_contains_specs_path_comment(self, tmp_cwd):
        result = run_init("myproject", "--template", "python-fasthtml")
        assert result.returncode == 0
        content = (tmp_cwd / "myproject" / "arrangement.yaml").read_text()
        assert "specs_path" in content

    def test_nextjs_template_contains_specs_path_comment(self, tmp_cwd):
        result = run_init("myproject", "--template", "nextjs-vitest")
        assert result.returncode == 0
        content = (tmp_cwd / "myproject" / "arrangement.yaml").read_text()
        assert "specs_path" in content
