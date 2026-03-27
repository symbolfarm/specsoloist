"""Tests for the build_diff module."""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from specsoloist.build_diff import (
    DiffResult,
    DiffSummary,
    BuildRun,
    normalize_source,
    compare_files,
    compare_directories,
    list_build_runs,
    record_build_run,
    run_diff,
)


class TestNormalizeSource:
    """Tests for the normalize_source function."""

    def test_python_with_comments(self):
        """Python files should have comments stripped via AST."""
        content = b"x = 1  # comment\n"
        result = normalize_source(content, "test.py")
        # AST unparse removes comments
        assert b"#" not in result
        assert b"x = 1" in result or b"x=1" in result

    def test_python_with_docstring(self):
        """Python files should have docstrings removed via AST."""
        content = b'def f():\n    """Doc"""\n    pass\n'
        result = normalize_source(content, "test.py")
        assert b'"""' not in result

    def test_python_syntax_error_fallback(self):
        """Python files with syntax errors fall back to comment stripping."""
        content = b"this is not valid python @@\n"
        result = normalize_source(content, "test.py")
        # Should fall back without raising
        assert isinstance(result, bytes)

    def test_python_inline_comment_stripping(self):
        """Comment stripping preserves code before # when AST fails."""
        content = b"x = 1  # this is a comment\n"
        result = normalize_source(content, "test.py")
        assert b"x" in result

    def test_javascript_line_comments(self):
        """JavaScript files should have // comments removed."""
        content = b"const x = 1;  // comment\n"
        result = normalize_source(content, "test.js")
        assert b"//" not in result
        assert b"const x = 1;" in result

    def test_javascript_block_comments(self):
        """JavaScript files should have /* */ comments removed."""
        content = b"/* comment */\nconst x = 1;\n"
        result = normalize_source(content, "test.js")
        assert b"/*" not in result
        assert b"*/" not in result
        assert b"const x = 1;" in result

    def test_typescript_comments(self):
        """TypeScript files use same comment stripping as JavaScript."""
        content = b"// comment\nconst x: number = 1;\n"
        result = normalize_source(content, "test.ts")
        assert b"//" not in result
        assert b"const x: number = 1;" in result

    def test_whitespace_normalization(self):
        """All text files should have whitespace normalized."""
        content = b"line1  \nline2\t\n\n"
        result = normalize_source(content, "test.txt")
        lines = result.decode('utf-8').split('\n')
        # Trailing whitespace should be stripped
        assert lines[0] == "line1"
        assert lines[1] == "line2"

    def test_binary_file_unchanged(self):
        """Binary files should be returned unchanged."""
        content = b"\x89PNG\r\n\x1a\n"
        result = normalize_source(content, "image.png")
        assert result == content

    def test_line_ending_normalization(self):
        """Line endings should be normalized to \\n."""
        content = b"line1\r\nline2\r\nline3"
        result = normalize_source(content, "test.txt")
        assert b"\r\n" not in result
        assert result == b"line1\nline2\nline3"


class TestCompareFiles:
    """Tests for the compare_files function."""

    def test_missing_left(self, tmp_path):
        """Return MISSING_LEFT when left file doesn't exist."""
        right_file = tmp_path / "right.txt"
        right_file.write_text("content")

        result = compare_files(
            str(tmp_path / "nonexistent.txt"),
            str(right_file),
            "file.txt"
        )
        assert result.status == "MISSING_LEFT"
        assert result.path == "file.txt"
        assert result.diff is None

    def test_missing_right(self, tmp_path):
        """Return MISSING_RIGHT when right file doesn't exist."""
        left_file = tmp_path / "left.txt"
        left_file.write_text("content")

        result = compare_files(
            str(left_file),
            str(tmp_path / "nonexistent.txt"),
            "file.txt"
        )
        assert result.status == "MISSING_RIGHT"
        assert result.path == "file.txt"
        assert result.diff is None

    def test_identical_files(self, tmp_path):
        """Return PASS when normalized content is identical."""
        left_file = tmp_path / "left.py"
        left_file.write_text("x = 1  # comment\n")

        right_file = tmp_path / "right.py"
        right_file.write_text("x = 1\n")

        result = compare_files(
            str(left_file),
            str(right_file),
            "file.py"
        )
        assert result.status == "PASS"
        assert result.diff is None

    def test_different_files(self, tmp_path):
        """Return FAIL with diff when files differ semantically."""
        left_file = tmp_path / "left.py"
        left_file.write_text("x = 1\n")

        right_file = tmp_path / "right.py"
        right_file.write_text("x = 2\n")

        result = compare_files(
            str(left_file),
            str(right_file),
            "file.py"
        )
        assert result.status == "FAIL"
        assert result.diff is not None
        assert "x = 1" in result.diff
        assert "x = 2" in result.diff

    def test_diff_shows_original_content(self, tmp_path):
        """Diff should show original (un-normalized) content."""
        left_file = tmp_path / "left.py"
        left_file.write_text("x = 1  # comment\n")

        right_file = tmp_path / "right.py"
        right_file.write_text("x = 2\n")

        result = compare_files(
            str(left_file),
            str(right_file),
            "file.py"
        )
        assert result.status == "FAIL"
        assert "# comment" in result.diff  # Original content shown


class TestCompareDirectories:
    """Tests for the compare_directories function."""

    def test_empty_directories(self, tmp_path):
        """Empty directories should produce all-zero summary."""
        left_dir = tmp_path / "left"
        right_dir = tmp_path / "right"
        left_dir.mkdir()
        right_dir.mkdir()

        summary = compare_directories(str(left_dir), str(right_dir))
        assert summary.passed == 0
        assert summary.failed == 0
        assert summary.missing_left == 0
        assert summary.missing_right == 0
        assert len(summary.results) == 0

    def test_ignored_patterns(self, tmp_path):
        """Ignored patterns should not be compared."""
        left_dir = tmp_path / "left"
        left_dir.mkdir()
        (left_dir / "__pycache__").mkdir()
        (left_dir / "__pycache__" / "test.pyc").write_text("pyc")
        (left_dir / ".git").mkdir()
        (left_dir / ".git" / "config").write_text("git")
        (left_dir / "node_modules").mkdir()
        (left_dir / "node_modules" / "pkg").mkdir()
        (left_dir / "node_modules" / "pkg" / "index.js").write_text("js")
        (left_dir / ".DS_Store").write_text("ds")
        (left_dir / "run_meta.json").write_text("{}")
        (left_dir / "test.spec.md").write_text("spec")

        right_dir = tmp_path / "right"
        right_dir.mkdir()

        summary = compare_directories(str(left_dir), str(right_dir))
        assert len(summary.results) == 0

    def test_nested_files(self, tmp_path):
        """Nested files should be compared with relative paths."""
        left_dir = tmp_path / "left"
        left_dir.mkdir()
        (left_dir / "subdir").mkdir()
        (left_dir / "subdir" / "file.py").write_text("x = 1")

        right_dir = tmp_path / "right"
        right_dir.mkdir()
        (right_dir / "subdir").mkdir()
        (right_dir / "subdir" / "file.py").write_text("x = 1")

        summary = compare_directories(str(left_dir), str(right_dir))
        assert summary.passed == 1
        assert summary.results[0].path == os.path.join("subdir", "file.py")

    def test_mixed_results(self, tmp_path):
        """Summary should count all result types."""
        left_dir = tmp_path / "left"
        left_dir.mkdir()
        (left_dir / "pass.py").write_text("x = 1")
        (left_dir / "fail.py").write_text("x = 1")
        (left_dir / "only_left.py").write_text("x = 1")

        right_dir = tmp_path / "right"
        right_dir.mkdir()
        (right_dir / "pass.py").write_text("x = 1")
        (right_dir / "fail.py").write_text("x = 2")
        (right_dir / "only_right.py").write_text("y = 2")

        summary = compare_directories(str(left_dir), str(right_dir))
        assert summary.passed == 1
        assert summary.failed == 1
        assert summary.missing_left == 1
        assert summary.missing_right == 1
        assert len(summary.results) == 4

    def test_custom_labels(self, tmp_path):
        """Custom labels should be stored in summary."""
        left_dir = tmp_path / "left"
        left_dir.mkdir()
        right_dir = tmp_path / "right"
        right_dir.mkdir()

        summary = compare_directories(str(left_dir), str(right_dir),
                                     label_left="v1", label_right="v2")
        assert summary.label_left == "v1"
        assert summary.label_right == "v2"

    def test_deterministic_ordering(self, tmp_path):
        """Results should be sorted by path deterministically."""
        left_dir = tmp_path / "left"
        left_dir.mkdir()
        (left_dir / "z.py").write_text("x = 1")
        (left_dir / "a.py").write_text("x = 1")
        (left_dir / "m.py").write_text("x = 1")

        right_dir = tmp_path / "right"
        right_dir.mkdir()
        (right_dir / "z.py").write_text("x = 1")
        (right_dir / "a.py").write_text("x = 1")
        (right_dir / "m.py").write_text("x = 1")

        summary = compare_directories(str(left_dir), str(right_dir))
        paths = [r.path for r in summary.results]
        assert paths == sorted(paths)


class TestListBuildRuns:
    """Tests for the list_build_runs function."""

    def test_nonexistent_directory(self):
        """Nonexistent build_dir should return empty list."""
        result = list_build_runs("/nonexistent/path")
        assert result == []

    def test_no_run_metadata(self, tmp_path):
        """Subdirectories without run_meta.json should be ignored."""
        (tmp_path / "subdir").mkdir()
        result = list_build_runs(str(tmp_path))
        assert result == []

    def test_single_run(self, tmp_path):
        """Single run with valid metadata should be discovered."""
        run_dir = tmp_path / "run-001"
        run_dir.mkdir()
        meta_file = run_dir / "run_meta.json"
        meta_file.write_text(json.dumps({
            "run_id": "2026-03-27T12-34-56",
            "timestamp": "2026-03-27T12:34:56Z",
        }))

        result = list_build_runs(str(tmp_path))
        assert len(result) == 1
        assert result[0].run_id == "2026-03-27T12-34-56"
        assert result[0].timestamp == "2026-03-27T12:34:56Z"
        assert result[0].path == str(run_dir)

    def test_metadata_with_optional_fields(self, tmp_path):
        """Metadata should include optional arrangement and meta fields."""
        run_dir = tmp_path / "run-001"
        run_dir.mkdir()
        meta_file = run_dir / "run_meta.json"
        meta_file.write_text(json.dumps({
            "run_id": "2026-03-27T12-34-56",
            "timestamp": "2026-03-27T12:34:56Z",
            "arrangement": "python",
            "custom_key": "custom_value",
        }))

        result = list_build_runs(str(tmp_path))
        assert result[0].arrangement == "python"
        assert result[0].meta.get("custom_key") == "custom_value"

    def test_sorted_by_timestamp(self, tmp_path):
        """Runs should be sorted by timestamp, oldest first."""
        for i, ts in enumerate(["2026-03-25T00:00:00Z", "2026-03-27T00:00:00Z", "2026-03-26T00:00:00Z"]):
            run_dir = tmp_path / f"run-{i:03d}"
            run_dir.mkdir()
            meta_file = run_dir / "run_meta.json"
            meta_file.write_text(json.dumps({
                "run_id": f"run-{i}",
                "timestamp": ts,
            }))

        result = list_build_runs(str(tmp_path))
        timestamps = [r.timestamp for r in result]
        assert timestamps == sorted(timestamps)

    def test_invalid_json_skipped(self, tmp_path):
        """Runs with invalid JSON should be silently skipped."""
        run_dir = tmp_path / "run-001"
        run_dir.mkdir()
        (run_dir / "run_meta.json").write_text("{invalid json")

        result = list_build_runs(str(tmp_path))
        assert result == []

    def test_missing_required_fields_skipped(self, tmp_path):
        """Runs missing run_id or timestamp should be skipped."""
        run_dir = tmp_path / "run-001"
        run_dir.mkdir()
        (run_dir / "run_meta.json").write_text(json.dumps({"run_id": "test"}))

        result = list_build_runs(str(tmp_path))
        assert result == []


class TestRecordBuildRun:
    """Tests for the record_build_run function."""

    def test_nonexistent_directory_raises(self, tmp_path):
        """Nonexistent output_dir should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            record_build_run(str(tmp_path / "nonexistent"))

    def test_creates_run_meta_json(self, tmp_path):
        """Should create run_meta.json in output_dir."""
        result = record_build_run(str(tmp_path))

        meta_file = tmp_path / "run_meta.json"
        assert meta_file.exists()

        with open(meta_file) as f:
            data = json.load(f)
        assert "run_id" in data
        assert "timestamp" in data

    def test_run_id_format(self, tmp_path):
        """Run ID should be ISO-8601 timestamp with colons replaced."""
        result = record_build_run(str(tmp_path))

        # run_id should not contain colons (they're replaced with hyphens)
        assert ":" not in result.run_id

    def test_timestamp_format(self, tmp_path):
        """Timestamp should be ISO-8601 format."""
        result = record_build_run(str(tmp_path))

        # Should be parseable as ISO-8601
        ts = datetime.fromisoformat(result.timestamp.rstrip('Z'))
        assert isinstance(ts, datetime)

    def test_arrangement_stored(self, tmp_path):
        """Optional arrangement should be stored."""
        result = record_build_run(str(tmp_path), arrangement="typescript")

        assert result.arrangement == "typescript"

        with open(tmp_path / "run_meta.json") as f:
            data = json.load(f)
        assert data["arrangement"] == "typescript"

    def test_meta_stored(self, tmp_path):
        """Optional meta dict should be stored."""
        result = record_build_run(str(tmp_path), meta={"custom": "value"})

        assert result.meta.get("custom") == "value"

        with open(tmp_path / "run_meta.json") as f:
            data = json.load(f)
        assert data["custom"] == "value"

    def test_returned_build_run(self, tmp_path):
        """Should return a BuildRun object with all metadata."""
        result = record_build_run(str(tmp_path), arrangement="py", meta={"version": "1.0"})

        assert isinstance(result, BuildRun)
        assert result.path == str(tmp_path)
        assert result.arrangement == "py"
        assert result.meta.get("version") == "1.0"


class TestRunDiff:
    """Tests for the run_diff function."""

    def test_creates_report_file(self, tmp_path, capsys):
        """Should create JSON report at report_path."""
        left_dir = tmp_path / "left"
        left_dir.mkdir()
        (left_dir / "test.py").write_text("x = 1")

        right_dir = tmp_path / "right"
        right_dir.mkdir()
        (right_dir / "test.py").write_text("x = 1")

        report_path = tmp_path / "reports" / "diff.json"

        summary = run_diff(str(left_dir), str(right_dir), str(report_path))

        assert report_path.exists()
        with open(report_path) as f:
            data = json.load(f)
        assert "passed" in data
        assert "failed" in data

    def test_report_data_structure(self, tmp_path):
        """Report should contain proper DiffSummary structure."""
        left_dir = tmp_path / "left"
        left_dir.mkdir()
        (left_dir / "pass.py").write_text("x = 1")
        (left_dir / "fail.py").write_text("x = 1")

        right_dir = tmp_path / "right"
        right_dir.mkdir()
        (right_dir / "pass.py").write_text("x = 1")
        (right_dir / "fail.py").write_text("x = 2")

        report_path = tmp_path / "diff.json"

        summary = run_diff(str(left_dir), str(right_dir), str(report_path))

        with open(report_path) as f:
            data = json.load(f)

        assert data["passed"] == 1
        assert data["failed"] == 1
        assert data["label_left"] == "left"
        assert data["label_right"] == "right"
        assert len(data["results"]) == 2

    def test_custom_labels_in_report(self, tmp_path):
        """Custom labels should appear in report."""
        left_dir = tmp_path / "left"
        left_dir.mkdir()
        right_dir = tmp_path / "right"
        right_dir.mkdir()

        report_path = tmp_path / "diff.json"

        summary = run_diff(str(left_dir), str(right_dir), str(report_path),
                          label_left="v1", label_right="v2")

        with open(report_path) as f:
            data = json.load(f)

        assert data["label_left"] == "v1"
        assert data["label_right"] == "v2"

    def test_returns_summary(self, tmp_path):
        """Should return DiffSummary object."""
        left_dir = tmp_path / "left"
        left_dir.mkdir()
        right_dir = tmp_path / "right"
        right_dir.mkdir()

        report_path = tmp_path / "diff.json"

        result = run_diff(str(left_dir), str(right_dir), str(report_path))

        assert isinstance(result, DiffSummary)
        assert isinstance(result.results, list)


# Parametrized tests for comprehensive coverage

class TestNormalizeSourceEdgeCases:
    """Edge case tests for normalize_source."""

    @pytest.mark.parametrize("filename,content,should_contain", [
        ("test.py", b"x = 1  # comment\ny = 2", b"y = 2"),
        ("test.js", b"// comment\nconst x = 1;", b"const x = 1;"),
        ("test.ts", b"/* block */\ntype X = number;", b"type X = number;"),
        ("test.tsx", b"// line\n<Component/>", b"<Component/>"),
        ("test.mjs", b"/* doc */\nexport const x = 1;", b"export const x = 1;"),
    ])
    def test_various_file_types(self, filename, content, should_contain):
        """Various file types should be normalized correctly."""
        result = normalize_source(content, filename)
        assert should_contain in result or should_contain in result


class TestCompareFilesEdgeCases:
    """Edge case tests for compare_files."""

    def test_binary_files_same(self, tmp_path):
        """Binary files with same content should PASS."""
        binary_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

        left_file = tmp_path / "left.png"
        left_file.write_bytes(binary_content)

        right_file = tmp_path / "right.png"
        right_file.write_bytes(binary_content)

        result = compare_files(str(left_file), str(right_file), "image.png")
        assert result.status == "PASS"

    def test_binary_files_different(self, tmp_path):
        """Binary files with different content should FAIL."""
        left_file = tmp_path / "left.png"
        left_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        right_file = tmp_path / "right.png"
        right_file.write_bytes(b"\x89JPG\r\n\x1a\n")

        result = compare_files(str(left_file), str(right_file), "image.png")
        assert result.status == "FAIL"
