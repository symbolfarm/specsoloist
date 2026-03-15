"""
Tests for spec_diff — spec vs code drift detection.
"""

import json
import os
import textwrap

import pytest

from specsoloist.spec_diff import (
    SpecDiffResult,
    SpecDiffIssue,
    extract_spec_symbols,
    extract_code_symbols,
    extract_test_names,
    extract_test_scenarios,
    format_result_json,
    format_result_text,
    diff_spec,
)
from specsoloist.parser import SpecParser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_file(tmp_path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content))
    return str(p)


def make_parsed_spec(tmp_path, spec_content: str, name: str = "myspec"):
    """Write a spec file and parse it."""
    spec_dir = tmp_path / "score"
    spec_dir.mkdir(exist_ok=True)
    (spec_dir / f"{name}.spec.md").write_text(textwrap.dedent(spec_content))
    parser = SpecParser(str(spec_dir))
    return parser.parse_spec(name)


# ---------------------------------------------------------------------------
# extract_code_symbols
# ---------------------------------------------------------------------------

class TestExtractCodeSymbols:
    def test_extracts_top_level_functions(self, tmp_path):
        code = """\
            def parse_spec(name):
                pass

            def validate(name):
                pass
        """
        path = write_file(tmp_path, "parser.py", code)
        symbols = extract_code_symbols(path)
        assert "parse_spec" in symbols
        assert "validate" in symbols

    def test_extracts_classes(self, tmp_path):
        code = """\
            class SpecParser:
                pass
        """
        path = write_file(tmp_path, "parser.py", code)
        assert "SpecParser" in extract_code_symbols(path)

    def test_does_not_extract_nested_functions(self, tmp_path):
        code = """\
            def outer():
                def inner():
                    pass
        """
        path = write_file(tmp_path, "x.py", code)
        symbols = extract_code_symbols(path)
        assert "outer" in symbols
        assert "inner" not in symbols

    def test_missing_file_returns_empty(self, tmp_path):
        assert extract_code_symbols(str(tmp_path / "nonexistent.py")) == []

    def test_syntax_error_returns_empty(self, tmp_path):
        path = write_file(tmp_path, "bad.py", "def this is not valid python!!!")
        assert extract_code_symbols(path) == []


# ---------------------------------------------------------------------------
# extract_spec_symbols
# ---------------------------------------------------------------------------

class TestExtractSpecSymbols:
    def test_bundle_yaml_functions(self, tmp_path):
        spec = """\
            ---
            name: mybundle
            type: bundle
            ---

            # Overview

            A bundle of utilities.

            # Functions

            ```yaml:functions
            parse_spec:
              inputs: {name: string}
              outputs: {result: object}
              behavior: "Parses a spec file"
            validate:
              inputs: {name: string}
              outputs: {valid: boolean}
              behavior: "Validates a spec"
            ```
        """
        parsed = make_parsed_spec(tmp_path, spec, "mybundle")
        symbols = extract_spec_symbols(parsed)
        assert "parse_spec" in symbols
        assert "validate" in symbols

    def test_function_spec_returns_name(self, tmp_path):
        spec = """\
            ---
            name: compute_hash
            type: function
            ---

            # Overview

            Computes a hash.

            # Behavior

            - Returns sha256 digest.
        """
        parsed = make_parsed_spec(tmp_path, spec, "compute_hash")
        symbols = extract_spec_symbols(parsed)
        assert "compute_hash" in symbols

    def test_module_spec_heading_symbols(self, tmp_path):
        spec = """\
            ---
            name: manifest
            type: module
            ---

            # Overview

            Build manifest.

            # Functions

            ## compute_file_hash(path) -> string

            Returns sha256.

            ## compute_content_hash(content) -> string

            Returns sha256 of string.
        """
        parsed = make_parsed_spec(tmp_path, spec, "manifest")
        symbols = extract_spec_symbols(parsed)
        assert "compute_file_hash" in symbols
        assert "compute_content_hash" in symbols
        # Section headers should not appear
        assert "Functions" not in symbols
        assert "Overview" not in symbols

    def test_reference_spec_returns_empty(self, tmp_path):
        spec = """\
            ---
            name: somelib
            type: reference
            ---

            # Overview

            Third-party library docs.

            # API

            Some API.
        """
        parsed = make_parsed_spec(tmp_path, spec, "somelib")
        symbols = extract_spec_symbols(parsed)
        assert symbols == []


# ---------------------------------------------------------------------------
# diff_spec integration
# ---------------------------------------------------------------------------

class TestDiffSpec:
    def _setup_project(self, tmp_path, spec_content, code_content=None, test_content=None, spec_name="mymod"):
        """Set up a minimal project directory for diff_spec tests."""
        # Score directory (specs)
        score_dir = tmp_path / "score"
        score_dir.mkdir()
        (score_dir / f"{spec_name}.spec.md").write_text(textwrap.dedent(spec_content))

        # Source file
        src_dir = tmp_path / "src" / "specsoloist"
        src_dir.mkdir(parents=True)
        if code_content is not None:
            (src_dir / f"{spec_name}.py").write_text(textwrap.dedent(code_content))

        # Test file
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        if test_content is not None:
            (tests_dir / f"test_{spec_name}.py").write_text(textwrap.dedent(test_content))

        return str(tmp_path)

    def test_no_issues_when_in_sync(self, tmp_path):
        root = self._setup_project(
            tmp_path,
            spec_content="""\
                ---
                name: mymod
                type: bundle
                ---

                # Overview

                My module.

                # Functions

                ```yaml:functions
                do_thing:
                  inputs: {}
                  outputs: {}
                  behavior: "Does a thing"
                ```
            """,
            code_content="""\
                def do_thing():
                    pass
            """,
        )
        result = diff_spec("mymod", root)
        missing = [i for i in result.issues if i.kind == "MISSING"]
        assert missing == [], f"Unexpected MISSING issues: {missing}"

    def test_reports_missing_symbol(self, tmp_path):
        root = self._setup_project(
            tmp_path,
            spec_content="""\
                ---
                name: mymod
                type: bundle
                ---

                # Overview

                My module.

                # Functions

                ```yaml:functions
                declared_func:
                  inputs: {}
                  outputs: {}
                  behavior: "Does stuff"
                ```
            """,
            code_content="""\
                def something_else():
                    pass
            """,
        )
        result = diff_spec("mymod", root)
        kinds = [i.kind for i in result.issues]
        symbols = [i.symbol for i in result.issues]
        assert "MISSING" in kinds
        assert "declared_func" in symbols

    def test_reports_undocumented_symbol(self, tmp_path):
        root = self._setup_project(
            tmp_path,
            spec_content="""\
                ---
                name: mymod
                type: bundle
                ---

                # Overview

                My module.

                # Functions

                ```yaml:functions
                declared_func:
                  inputs: {}
                  outputs: {}
                  behavior: "Does stuff"
                ```
            """,
            code_content="""\
                def declared_func():
                    pass

                def undocumented_public():
                    pass
            """,
        )
        result = diff_spec("mymod", root)
        kinds = [i.kind for i in result.issues]
        symbols = [i.symbol for i in result.issues]
        assert "UNDOCUMENTED" in kinds
        assert "undocumented_public" in symbols

    def test_private_symbols_not_flagged_as_undocumented(self, tmp_path):
        root = self._setup_project(
            tmp_path,
            spec_content="""\
                ---
                name: mymod
                type: bundle
                ---

                # Overview

                My module.

                # Functions

                ```yaml:functions
                declared_func:
                  inputs: {}
                  outputs: {}
                  behavior: "Does stuff"
                ```
            """,
            code_content="""\
                def declared_func():
                    pass

                def _private_helper():
                    pass
            """,
        )
        result = diff_spec("mymod", root)
        symbols = [i.symbol for i in result.issues]
        assert "_private_helper" not in symbols


# ---------------------------------------------------------------------------
# format_result_json
# ---------------------------------------------------------------------------

class TestFormatResultJson:
    def test_json_is_parseable(self):
        result = SpecDiffResult(
            spec_name="parser",
            code_path="/some/path.py",
            test_path=None,
            issues=[
                SpecDiffIssue(kind="MISSING", symbol="parse_spec", detail="not in code"),
            ],
        )
        output = format_result_json(result)
        data = json.loads(output)
        assert data["spec_name"] == "parser"
        assert data["issue_count"] == 1
        assert data["issues"][0]["kind"] == "MISSING"
        assert data["issues"][0]["symbol"] == "parse_spec"

    def test_json_no_issues(self):
        result = SpecDiffResult(
            spec_name="manifest",
            code_path="/some/manifest.py",
            test_path=None,
        )
        output = format_result_json(result)
        data = json.loads(output)
        assert data["issue_count"] == 0
        assert data["issues"] == []


# ---------------------------------------------------------------------------
# format_result_text
# ---------------------------------------------------------------------------

class TestFormatResultText:
    def test_clean_message_when_no_issues(self):
        result = SpecDiffResult(spec_name="manifest", code_path=None, test_path=None)
        text = format_result_text(result)
        assert "no issues" in text
        assert "manifest" in text

    def test_shows_missing_marker(self):
        result = SpecDiffResult(
            spec_name="parser",
            code_path="/p.py",
            test_path=None,
            issues=[SpecDiffIssue(kind="MISSING", symbol="parse_spec", detail="not found")],
        )
        text = format_result_text(result)
        assert "MISSING" in text
        assert "parse_spec" in text

    def test_shows_undocumented_marker(self):
        result = SpecDiffResult(
            spec_name="parser",
            code_path="/p.py",
            test_path=None,
            issues=[SpecDiffIssue(kind="UNDOCUMENTED", symbol="_hidden", detail="in code")],
        )
        text = format_result_text(result)
        assert "UNDOCUMENTED" in text

    def test_shows_test_gap_marker(self):
        result = SpecDiffResult(
            spec_name="parser",
            code_path="/p.py",
            test_path="/t.py",
            issues=[SpecDiffIssue(kind="TEST_GAP", symbol='"some scenario"', detail="no test")],
        )
        text = format_result_text(result)
        assert "TEST GAP" in text


# ---------------------------------------------------------------------------
# CLI integration (smoke test)
# ---------------------------------------------------------------------------

class TestCLISpDiff:
    def test_help_output(self):
        """sp diff --help should mention spec-drift mode."""
        import subprocess
        result = subprocess.run(
            ["uv", "run", "sp", "diff", "--help"],
            capture_output=True, text=True,
            cwd="/home/toby/_code/symbolfarm/specsoloist"
        )
        assert result.returncode == 0
        assert "diff" in result.stdout.lower()

    def test_spec_diff_runs_on_known_spec(self):
        """sp diff parser should run without crashing on the framework's own parser spec."""
        import subprocess
        result = subprocess.run(
            ["uv", "run", "sp", "diff", "parser"],
            capture_output=True, text=True,
            cwd="/home/toby/_code/symbolfarm/specsoloist"
        )
        # Should not raise an unhandled exception (output may have issues but mustn't crash)
        assert result.returncode in (0, 1), f"Unexpected exit code: {result.returncode}\n{result.stderr}"
        # Output should mention the spec name
        assert "parser" in result.stdout

    def test_json_flag_produces_valid_json(self):
        """sp diff parser --json should produce valid JSON."""
        import subprocess
        result = subprocess.run(
            ["uv", "run", "sp", "diff", "parser", "--json"],
            capture_output=True, text=True,
            cwd="/home/toby/_code/symbolfarm/specsoloist"
        )
        assert result.returncode in (0, 1)
        data = json.loads(result.stdout)
        assert "spec_name" in data
        assert "issues" in data
