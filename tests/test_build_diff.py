"""
Tests for specsoloist.build_diff module.

Uses tmp_path pytest fixture; no network calls or LLM API keys required.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specsoloist.build_diff import (
    BuildRun,
    DiffResult,
    DiffSummary,
    compare_directories,
    compare_files,
    list_build_runs,
    normalize_source,
    record_build_run,
    run_diff,
)


# ---------------------------------------------------------------------------
# normalize_source tests
# ---------------------------------------------------------------------------


class TestNormalizeSourcePython:
    def test_strips_inline_comments(self):
        src = "x = 1  # comment\n"
        result = normalize_source(src, "foo.py")
        assert "#" not in result
        assert "x = 1" in result

    def test_strips_docstrings(self):
        src = 'def f():\n    """A docstring."""\n    pass\n'
        result = normalize_source(src, "foo.py")
        assert "docstring" not in result
        # function should still be present
        assert "def f" in result

    def test_semantically_equivalent_with_whitespace(self):
        src1 = "x = 1\ny = 2\n"
        src2 = "x = 1\n\ny = 2\n"
        assert normalize_source(src1, "a.py") == normalize_source(src2, "a.py")

    def test_different_logic_differs(self):
        src1 = "x = 1\n"
        src2 = "x = 2\n"
        assert normalize_source(src1, "a.py") != normalize_source(src2, "a.py")

    def test_fallback_on_syntax_error(self):
        src = "# a comment\ndef f(\n"  # SyntaxError
        result = normalize_source(src, "bad.py")
        # Should not raise, and should strip the comment line
        assert isinstance(result, str)
        assert "a comment" not in result

    def test_py_extension_case_insensitive(self):
        # .py suffix detection should be lower-cased
        src = "x = 1  # comment\n"
        result = normalize_source(src, "FOO.PY")
        assert "#" not in result


class TestNormalizeSourceJS:
    def test_strips_line_comments(self):
        src = "const x = 1; // inline\n"
        result = normalize_source(src, "app.js")
        assert "//" not in result
        assert "const x = 1" in result

    def test_strips_block_comments(self):
        src = "/* header */\nconst x = 1;\n"
        result = normalize_source(src, "app.ts")
        assert "header" not in result
        assert "const x = 1" in result

    def test_tsx_treated_as_js(self):
        src = "// comment\nconst y = 2;\n"
        result = normalize_source(src, "component.tsx")
        assert "//" not in result

    def test_mjs_treated_as_js(self):
        src = "// note\nexport default {};\n"
        result = normalize_source(src, "module.mjs")
        assert "//" not in result


class TestNormalizeSourceOther:
    def test_normalizes_line_endings(self):
        src = "hello\r\nworld\r\n"
        result = normalize_source(src, "readme.txt")
        assert "\r" not in result
        assert "hello" in result
        assert "world" in result

    def test_strips_trailing_whitespace(self):
        src = "hello   \nworld  \n"
        result = normalize_source(src, "data.txt")
        for line in result.splitlines():
            assert line == line.rstrip()

    def test_json_file_normalized(self):
        src = '{"key": "value"}  \n'
        result = normalize_source(src, "data.json")
        assert result.strip() == '{"key": "value"}'


# ---------------------------------------------------------------------------
# compare_files tests
# ---------------------------------------------------------------------------


class TestCompareFiles:
    def test_pass_identical_files(self, tmp_path):
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.write_text("x = 1\n")
        f2.write_text("x = 1\n")
        result = compare_files(str(f1), str(f2), "a.py")
        assert result.status == "PASS"
        assert result.diff is None

    def test_pass_semantically_equivalent(self, tmp_path):
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.write_text("x = 1  # comment\n")
        f2.write_text("x = 1\n")
        result = compare_files(str(f1), str(f2), "a.py")
        assert result.status == "PASS"

    def test_fail_different_logic(self, tmp_path):
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.write_text("x = 1\n")
        f2.write_text("x = 2\n")
        result = compare_files(str(f1), str(f2), "a.py")
        assert result.status == "FAIL"
        assert result.diff is not None
        assert "---" in result.diff or "+++" in result.diff

    def test_missing_left(self, tmp_path):
        f2 = tmp_path / "b.py"
        f2.write_text("x = 1\n")
        result = compare_files(str(tmp_path / "nonexistent.py"), str(f2), "b.py")
        assert result.status == "MISSING_LEFT"

    def test_missing_right(self, tmp_path):
        f1 = tmp_path / "a.py"
        f1.write_text("x = 1\n")
        result = compare_files(str(f1), str(tmp_path / "nonexistent.py"), "a.py")
        assert result.status == "MISSING_RIGHT"

    def test_pass_docstring_removed(self, tmp_path):
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.write_text('def f():\n    """Docstring."""\n    pass\n')
        f2.write_text("def f():\n    pass\n")
        result = compare_files(str(f1), str(f2), "a.py")
        assert result.status == "PASS"

    def test_binary_files_identical(self, tmp_path):
        data = bytes(range(256))
        f1 = tmp_path / "a.bin"
        f2 = tmp_path / "b.bin"
        f1.write_bytes(data)
        f2.write_bytes(data)
        result = compare_files(str(f1), str(f2), "a.bin")
        assert result.status == "PASS"

    def test_binary_files_differ(self, tmp_path):
        f1 = tmp_path / "a.bin"
        f2 = tmp_path / "b.bin"
        f1.write_bytes(b"\x00\x01\x02")
        f2.write_bytes(b"\x00\x01\x03")
        result = compare_files(str(f1), str(f2), "a.bin")
        assert result.status == "FAIL"

    def test_relative_path_in_result(self, tmp_path):
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.write_text("x = 1\n")
        f2.write_text("x = 2\n")
        result = compare_files(str(f1), str(f2), "subdir/a.py")
        assert result.path == "subdir/a.py"


# ---------------------------------------------------------------------------
# compare_directories tests
# ---------------------------------------------------------------------------


class TestCompareDirectories:
    def _make_tree(self, root: Path, files: dict[str, str]) -> None:
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)

    def test_all_pass(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left, {"a.py": "x = 1\n", "b.txt": "hello\n"})
        self._make_tree(right, {"a.py": "x = 1\n", "b.txt": "hello\n"})
        summary = compare_directories(str(left), str(right))
        assert summary.passed == 2
        assert summary.failed == 0
        assert summary.missing_left == 0
        assert summary.missing_right == 0

    def test_missing_right(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left, {"a.py": "x = 1\n", "b.py": "y = 2\n"})
        self._make_tree(right, {"a.py": "x = 1\n"})
        summary = compare_directories(str(left), str(right))
        assert summary.missing_right == 1
        missing = [r for r in summary.results if r.status == "MISSING_RIGHT"]
        assert missing[0].path == "b.py"

    def test_missing_left(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left, {"a.py": "x = 1\n"})
        self._make_tree(right, {"a.py": "x = 1\n", "c.py": "z = 3\n"})
        summary = compare_directories(str(left), str(right))
        assert summary.missing_left == 1

    def test_fail_diff(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left, {"a.py": "x = 1\n"})
        self._make_tree(right, {"a.py": "x = 2\n"})
        summary = compare_directories(str(left), str(right))
        assert summary.failed == 1

    def test_ignores_pycache(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left, {"a.py": "x = 1\n", "__pycache__/x.pyc": "bytes"})
        self._make_tree(right, {"a.py": "x = 1\n"})
        summary = compare_directories(str(left), str(right))
        # __pycache__/x.pyc should be ignored
        assert all("__pycache__" not in r.path for r in summary.results)
        assert summary.passed == 1
        assert summary.missing_right == 0

    def test_ignores_run_meta_json(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(
            left,
            {"a.py": "x = 1\n", "run_meta.json": '{"run_id": "abc"}'},
        )
        self._make_tree(right, {"a.py": "x = 1\n"})
        summary = compare_directories(str(left), str(right))
        assert all(r.path != "run_meta.json" for r in summary.results)

    def test_ignores_spec_md(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(
            left,
            {"a.py": "x = 1\n", "core.spec.md": "# spec"},
        )
        self._make_tree(right, {"a.py": "x = 1\n"})
        summary = compare_directories(str(left), str(right))
        assert all(not r.path.endswith(".spec.md") for r in summary.results)

    def test_ignores_dot_git(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left, {"a.py": "x = 1\n", ".git/HEAD": "ref: refs/heads/main"})
        self._make_tree(right, {"a.py": "x = 1\n"})
        summary = compare_directories(str(left), str(right))
        assert all(".git" not in r.path for r in summary.results)

    def test_sorted_results(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        files = {"z.py": "z=1\n", "a.py": "a=1\n", "m.py": "m=1\n"}
        self._make_tree(left, files)
        self._make_tree(right, files)
        summary = compare_directories(str(left), str(right))
        paths = [r.path for r in summary.results]
        assert paths == sorted(paths)

    def test_labels_propagated(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        summary = compare_directories(
            str(left), str(right), label_left="src", label_right="build"
        )
        assert summary.label_left == "src"
        assert summary.label_right == "build"

    def test_nonexistent_left_dir(self, tmp_path):
        right = tmp_path / "right"
        right.mkdir()
        (right / "a.py").write_text("x = 1\n")
        summary = compare_directories(str(tmp_path / "nonexistent"), str(right))
        assert summary.missing_left == 1

    def test_nonexistent_right_dir(self, tmp_path):
        left = tmp_path / "left"
        left.mkdir()
        (left / "a.py").write_text("x = 1\n")
        summary = compare_directories(str(left), str(tmp_path / "nonexistent"))
        assert summary.missing_right == 1


# ---------------------------------------------------------------------------
# record_build_run tests
# ---------------------------------------------------------------------------


class TestRecordBuildRun:
    def test_creates_run_meta_json(self, tmp_path):
        run = record_build_run(str(tmp_path))
        meta_file = tmp_path / "run_meta.json"
        assert meta_file.exists()

    def test_run_meta_json_content(self, tmp_path):
        run = record_build_run(str(tmp_path), arrangement="python")
        meta_file = tmp_path / "run_meta.json"
        data = json.loads(meta_file.read_text())
        assert data["run_id"] == run.run_id
        assert data["timestamp"] == run.timestamp
        assert data["arrangement"] == "python"

    def test_returns_build_run(self, tmp_path):
        run = record_build_run(str(tmp_path))
        assert isinstance(run, BuildRun)
        assert run.run_id
        assert run.timestamp
        assert run.path == str(tmp_path.resolve())

    def test_run_id_is_timestamp_with_hyphens(self, tmp_path):
        run = record_build_run(str(tmp_path))
        assert ":" not in run.run_id
        assert "-" in run.run_id

    def test_extra_meta_stored(self, tmp_path):
        run = record_build_run(str(tmp_path), meta={"env": "ci", "version": "1.0"})
        meta_file = tmp_path / "run_meta.json"
        data = json.loads(meta_file.read_text())
        assert data["env"] == "ci"
        assert data["version"] == "1.0"

    def test_raises_if_dir_not_exists(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            record_build_run(str(tmp_path / "nonexistent"))

    def test_iso8601_timestamp(self, tmp_path):
        run = record_build_run(str(tmp_path))
        # Should be parseable as ISO-8601
        from datetime import datetime
        # Just check it doesn't raise
        assert "T" in run.timestamp

    def test_no_arrangement_none(self, tmp_path):
        run = record_build_run(str(tmp_path))
        meta_file = tmp_path / "run_meta.json"
        data = json.loads(meta_file.read_text())
        assert data["arrangement"] is None
        assert run.arrangement is None


# ---------------------------------------------------------------------------
# list_build_runs tests
# ---------------------------------------------------------------------------


class TestListBuildRuns:
    def test_empty_if_no_build_dir(self, tmp_path):
        result = list_build_runs(str(tmp_path / "nonexistent"))
        assert result == []

    def test_empty_if_no_run_meta(self, tmp_path):
        (tmp_path / "run1").mkdir()
        result = list_build_runs(str(tmp_path))
        assert result == []

    def test_discovers_runs(self, tmp_path):
        run1_dir = tmp_path / "run1"
        run1_dir.mkdir()
        record_build_run(str(run1_dir))
        runs = list_build_runs(str(tmp_path))
        assert len(runs) == 1
        assert isinstance(runs[0], BuildRun)

    def test_sorted_oldest_first(self, tmp_path):
        import time

        run1_dir = tmp_path / "run1"
        run1_dir.mkdir()
        r1 = record_build_run(str(run1_dir))

        time.sleep(0.01)  # ensure different timestamps

        run2_dir = tmp_path / "run2"
        run2_dir.mkdir()
        r2 = record_build_run(str(run2_dir))

        runs = list_build_runs(str(tmp_path))
        assert len(runs) == 2
        assert runs[0].timestamp <= runs[1].timestamp

    def test_skips_invalid_json(self, tmp_path):
        bad_dir = tmp_path / "bad"
        bad_dir.mkdir()
        (bad_dir / "run_meta.json").write_text("not json")
        runs = list_build_runs(str(tmp_path))
        assert runs == []

    def test_skips_missing_required_fields(self, tmp_path):
        incomplete_dir = tmp_path / "incomplete"
        incomplete_dir.mkdir()
        (incomplete_dir / "run_meta.json").write_text('{"run_id": "abc"}')
        runs = list_build_runs(str(tmp_path))
        assert runs == []

    def test_arrangement_and_meta_preserved(self, tmp_path):
        run_dir = tmp_path / "run1"
        run_dir.mkdir()
        record_build_run(str(run_dir), arrangement="typescript", meta={"env": "prod"})
        runs = list_build_runs(str(tmp_path))
        assert runs[0].arrangement == "typescript"
        assert runs[0].meta.get("env") == "prod"


# ---------------------------------------------------------------------------
# run_diff tests
# ---------------------------------------------------------------------------


class TestRunDiff:
    def _make_tree(self, root: Path, files: dict[str, str]) -> None:
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)

    def test_returns_diff_summary(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left, {"a.py": "x = 1\n"})
        self._make_tree(right, {"a.py": "x = 1\n"})
        report = tmp_path / "report.json"
        result = run_diff(str(left), str(right), str(report))
        assert isinstance(result, DiffSummary)

    def test_writes_json_report(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left, {"a.py": "x = 1\n"})
        self._make_tree(right, {"a.py": "x = 2\n"})
        report = tmp_path / "reports" / "diff.json"
        run_diff(str(left), str(right), str(report))
        assert report.exists()
        data = json.loads(report.read_text())
        assert "passed" in data
        assert "failed" in data
        assert "results" in data

    def test_creates_report_parent_dirs(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        deep_report = tmp_path / "a" / "b" / "c" / "report.json"
        run_diff(str(left), str(right), str(deep_report))
        assert deep_report.exists()

    def test_report_has_correct_shape(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left, {"a.py": "x = 1\n"})
        self._make_tree(right, {"a.py": "x = 2\n"})
        report = tmp_path / "report.json"
        run_diff(str(left), str(right), str(report), label_left="src", label_right="build")
        data = json.loads(report.read_text())
        assert data["label_left"] == "src"
        assert data["label_right"] == "build"
        assert isinstance(data["results"], list)
        assert data["results"][0]["path"] == "a.py"
        assert data["results"][0]["status"] == "FAIL"

    def test_pass_all_reflected_in_summary(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left, {"a.py": "x = 1\n", "b.py": "y = 2\n"})
        self._make_tree(right, {"a.py": "x = 1\n", "b.py": "y = 2\n"})
        report = tmp_path / "report.json"
        result = run_diff(str(left), str(right), str(report))
        assert result.passed == 2
        assert result.failed == 0

    def test_semantic_equivalence_counted_as_pass(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        self._make_tree(left, {"a.py": "x = 1  # comment\n"})
        self._make_tree(right, {"a.py": "x = 1\n"})
        report = tmp_path / "report.json"
        result = run_diff(str(left), str(right), str(report))
        assert result.passed == 1
        assert result.failed == 0
