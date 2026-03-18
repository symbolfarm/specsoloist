"""Tests for the build_diff module."""

import json
import os
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


class TestNormalizeSource:
    def test_python_strips_comments(self):
        code = "x = 1  # this is a comment\ny = 2\n"
        result = normalize_source(code, "foo.py")
        assert "#" not in result
        assert "x = 1" in result
        assert "y = 2" in result

    def test_python_strips_docstrings(self):
        code = 'def foo():\n    """This is a docstring."""\n    return 1\n'
        result = normalize_source(code, "foo.py")
        assert "docstring" not in result
        assert "return 1" in result

    def test_python_comments_same_logic(self):
        code1 = "x = 1  # comment\n"
        code2 = "x = 1\n"
        assert normalize_source(code1, "foo.py") == normalize_source(code2, "foo.py")

    def test_python_fallback_on_syntax_error(self):
        code = "def broken(\n    # incomplete\n"
        result = normalize_source(code, "foo.py")
        assert isinstance(result, str)  # Should not raise

    def test_typescript_strips_line_comments(self):
        code = "const x = 1; // comment\nconst y = 2;\n"
        result = normalize_source(code, "foo.ts")
        assert "// comment" not in result
        assert "const x = 1" in result

    def test_typescript_strips_block_comments(self):
        code = "/* block comment */\nconst x = 1;\n"
        result = normalize_source(code, "foo.ts")
        assert "block comment" not in result

    def test_other_files_normalize_endings(self):
        code = "line1\r\nline2\r\n"
        result = normalize_source(code, "foo.txt")
        assert "\r\n" not in result
        assert "line1" in result

    def test_js_extension(self):
        code = "const x = 1; // comment\n"
        result = normalize_source(code, "foo.js")
        assert "// comment" not in result


class TestCompareFiles:
    def test_pass_identical_files(self, tmp_path):
        left = tmp_path / "left.py"
        right = tmp_path / "right.py"
        left.write_text("x = 1\n")
        right.write_text("x = 1\n")
        result = compare_files(str(left), str(right), "test.py")
        assert result.status == "PASS"
        assert result.diff is None

    def test_pass_semantically_equal(self, tmp_path):
        left = tmp_path / "left.py"
        right = tmp_path / "right.py"
        left.write_text("x = 1  # comment\n")
        right.write_text("x = 1\n")
        result = compare_files(str(left), str(right), "test.py")
        assert result.status == "PASS"

    def test_fail_different_logic(self, tmp_path):
        left = tmp_path / "left.py"
        right = tmp_path / "right.py"
        left.write_text("x = 1\n")
        right.write_text("x = 2\n")
        result = compare_files(str(left), str(right), "test.py")
        assert result.status == "FAIL"
        assert result.diff is not None

    def test_missing_left(self, tmp_path):
        right = tmp_path / "right.py"
        right.write_text("x = 1\n")
        result = compare_files(str(tmp_path / "missing.py"), str(right), "test.py")
        assert result.status == "MISSING_LEFT"

    def test_missing_right(self, tmp_path):
        left = tmp_path / "left.py"
        left.write_text("x = 1\n")
        result = compare_files(str(left), str(tmp_path / "missing.py"), "test.py")
        assert result.status == "MISSING_RIGHT"

    def test_path_preserved(self, tmp_path):
        left = tmp_path / "left.py"
        right = tmp_path / "right.py"
        left.write_text("x = 1\n")
        right.write_text("x = 1\n")
        result = compare_files(str(left), str(right), "subdir/test.py")
        assert result.path == "subdir/test.py"


class TestCompareDirectories:
    def test_identical_directories(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        (left / "foo.py").write_text("x = 1\n")
        (right / "foo.py").write_text("x = 1\n")
        summary = compare_directories(str(left), str(right))
        assert summary.passed == 1
        assert summary.failed == 0

    def test_different_files(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        (left / "foo.py").write_text("x = 1\n")
        (right / "foo.py").write_text("x = 2\n")
        summary = compare_directories(str(left), str(right))
        assert summary.failed == 1

    def test_missing_in_right(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        (left / "foo.py").write_text("x = 1\n")
        summary = compare_directories(str(left), str(right))
        assert summary.missing_right == 1

    def test_missing_in_left(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        (right / "foo.py").write_text("x = 1\n")
        summary = compare_directories(str(left), str(right))
        assert summary.missing_left == 1

    def test_ignores_pycache(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        (left / "__pycache__").mkdir()
        (left / "__pycache__" / "foo.pyc").write_text("bytecode")
        (left / "real.py").write_text("x = 1\n")
        (right / "real.py").write_text("x = 1\n")
        summary = compare_directories(str(left), str(right))
        assert summary.passed == 1
        assert summary.failed == 0

    def test_ignores_spec_files(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        (left / "foo.spec.md").write_text("spec content")
        (right / "foo.spec.md").write_text("different spec content")
        (left / "real.py").write_text("x = 1\n")
        (right / "real.py").write_text("x = 1\n")
        summary = compare_directories(str(left), str(right))
        # spec files ignored, only real.py compared
        assert summary.passed == 1

    def test_labels(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        summary = compare_directories(str(left), str(right), "original", "quine")
        assert summary.label_left == "original"
        assert summary.label_right == "quine"

    def test_sorted_results(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        for name in ["c.py", "a.py", "b.py"]:
            (left / name).write_text("x = 1\n")
            (right / name).write_text("x = 1\n")
        summary = compare_directories(str(left), str(right))
        paths = [r.path for r in summary.results]
        assert paths == sorted(paths)


class TestListBuildRuns:
    def test_empty_dir(self, tmp_path):
        runs = list_build_runs(str(tmp_path))
        assert runs == []

    def test_nonexistent_dir(self, tmp_path):
        runs = list_build_runs(str(tmp_path / "nonexistent"))
        assert runs == []

    def test_finds_runs(self, tmp_path):
        run_dir = tmp_path / "run1"
        run_dir.mkdir()
        (run_dir / "run_meta.json").write_text(json.dumps({
            "run_id": "2024-01-01T00:00:00",
            "timestamp": "2024-01-01T00:00:00Z",
            "arrangement": "python",
        }))
        runs = list_build_runs(str(tmp_path))
        assert len(runs) == 1
        assert runs[0].run_id == "2024-01-01T00:00:00"

    def test_sorted_by_timestamp(self, tmp_path):
        for i, ts in enumerate(["2024-01-03T00:00:00Z", "2024-01-01T00:00:00Z"]):
            run_dir = tmp_path / f"run{i}"
            run_dir.mkdir()
            (run_dir / "run_meta.json").write_text(json.dumps({
                "run_id": f"run{i}",
                "timestamp": ts,
            }))
        runs = list_build_runs(str(tmp_path))
        assert runs[0].timestamp < runs[1].timestamp

    def test_skips_invalid_runs(self, tmp_path):
        run_dir = tmp_path / "bad_run"
        run_dir.mkdir()
        (run_dir / "run_meta.json").write_text("not valid json")
        runs = list_build_runs(str(tmp_path))
        assert len(runs) == 0


class TestRecordBuildRun:
    def test_creates_run_meta(self, tmp_path):
        run = record_build_run(str(tmp_path))
        assert (tmp_path / "run_meta.json").exists()
        assert isinstance(run, BuildRun)
        assert run.run_id is not None

    def test_includes_arrangement(self, tmp_path):
        run = record_build_run(str(tmp_path), arrangement="python")
        data = json.loads((tmp_path / "run_meta.json").read_text())
        assert data["arrangement"] == "python"

    def test_includes_meta(self, tmp_path):
        run = record_build_run(str(tmp_path), meta={"spec_count": 10})
        data = json.loads((tmp_path / "run_meta.json").read_text())
        assert data["spec_count"] == 10

    def test_missing_output_dir_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            record_build_run(str(tmp_path / "nonexistent"))


class TestRunDiff:
    def test_run_diff_creates_report(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        (left / "foo.py").write_text("x = 1\n")
        (right / "foo.py").write_text("x = 1\n")

        report_path = str(tmp_path / "report.json")
        summary = run_diff(str(left), str(right), report_path)

        assert os.path.exists(report_path)
        assert summary.passed == 1

    def test_run_diff_report_structure(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()
        (left / "foo.py").write_text("x = 1\n")
        (right / "foo.py").write_text("x = 1\n")

        report_path = str(tmp_path / "report.json")
        run_diff(str(left), str(right), report_path)

        data = json.loads(open(report_path).read())
        assert "passed" in data
        assert "failed" in data
        assert "results" in data

    def test_run_diff_returns_summary(self, tmp_path):
        left = tmp_path / "left"
        right = tmp_path / "right"
        left.mkdir()
        right.mkdir()

        report_path = str(tmp_path / "report.json")
        result = run_diff(str(left), str(right), report_path)
        assert isinstance(result, DiffSummary)
