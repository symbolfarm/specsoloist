"""Test suite for spec_diff module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from specsoloist.spec_diff import (
    SpecDiffIssue,
    SpecDiffResult,
    extract_spec_symbols,
    extract_code_symbols,
    extract_test_names,
    extract_test_scenarios,
    diff_spec,
    format_result_text,
    format_result_json,
)


class TestSpecDiffIssue:
    """Tests for SpecDiffIssue dataclass."""

    def test_create_issue(self):
        """Test creating a SpecDiffIssue."""
        issue = SpecDiffIssue(
            kind="MISSING",
            symbol="foo",
            detail="Symbol not found",
        )
        assert issue.kind == "MISSING"
        assert issue.symbol == "foo"
        assert issue.detail == "Symbol not found"


class TestSpecDiffResult:
    """Tests for SpecDiffResult dataclass."""

    def test_issue_count_empty(self):
        """Test issue_count property when no issues."""
        result = SpecDiffResult(spec_name="test")
        assert result.issue_count == 0

    def test_issue_count_with_issues(self):
        """Test issue_count property with multiple issues."""
        result = SpecDiffResult(spec_name="test")
        result.issues.append(SpecDiffIssue("MISSING", "foo", "not found"))
        result.issues.append(SpecDiffIssue("UNDOCUMENTED", "bar", "not declared"))
        assert result.issue_count == 2

    def test_to_dict(self):
        """Test to_dict serialization."""
        result = SpecDiffResult(
            spec_name="parser",
            code_path="/path/to/parser.py",
            test_path="/path/to/test_parser.py",
        )
        result.issues.append(
            SpecDiffIssue("MISSING", "extract_schema", "symbol missing")
        )

        d = result.to_dict()
        assert d["spec_name"] == "parser"
        assert d["code_path"] == "/path/to/parser.py"
        assert d["test_path"] == "/path/to/test_parser.py"
        assert d["issue_count"] == 1
        assert len(d["issues"]) == 1
        assert d["issues"][0]["kind"] == "MISSING"
        assert d["issues"][0]["symbol"] == "extract_schema"


class TestExtractCodeSymbols:
    """Tests for extract_code_symbols function."""

    def test_extract_top_level_functions(self):
        """Test extracting top-level function names."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
def foo():
    pass

def bar():
    pass
""")
            f.flush()
            try:
                symbols = extract_code_symbols(f.name)
                assert "foo" in symbols
                assert "bar" in symbols
            finally:
                os.unlink(f.name)

    def test_extract_class_names(self):
        """Test extracting class names."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
class MyClass:
    pass

class AnotherClass:
    pass
""")
            f.flush()
            try:
                symbols = extract_code_symbols(f.name)
                assert "MyClass" in symbols
                assert "AnotherClass" in symbols
            finally:
                os.unlink(f.name)

    def test_extract_class_methods(self):
        """Test extracting public methods from classes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
class MyClass:
    def __init__(self):
        pass

    def public_method(self):
        pass

    def _private_method(self):
        pass
""")
            f.flush()
            try:
                symbols = extract_code_symbols(f.name)
                assert "MyClass" in symbols
                assert "public_method" in symbols
                assert "__init__" in symbols
                assert "_private_method" not in symbols
            finally:
                os.unlink(f.name)

    def test_extract_async_functions(self):
        """Test extracting async functions."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
async def async_func():
    pass
""")
            f.flush()
            try:
                symbols = extract_code_symbols(f.name)
                assert "async_func" in symbols
            finally:
                os.unlink(f.name)

    def test_missing_file(self):
        """Test extracting from non-existent file."""
        symbols = extract_code_symbols("/nonexistent/path.py")
        assert symbols == []

    def test_syntax_error(self):
        """Test graceful handling of syntax errors."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def broken(: pass")
            f.flush()
            try:
                symbols = extract_code_symbols(f.name)
                assert symbols == []
            finally:
                os.unlink(f.name)

    def test_no_nested_functions(self):
        """Test that nested functions are not included."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
def outer():
    def inner():
        pass
    return inner
""")
            f.flush()
            try:
                symbols = extract_code_symbols(f.name)
                assert "outer" in symbols
                assert "inner" not in symbols
            finally:
                os.unlink(f.name)


class TestExtractTestNames:
    """Tests for extract_test_names function."""

    def test_extract_test_functions(self):
        """Test extracting test function names."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
def test_foo():
    pass

def test_bar():
    pass

def helper():
    pass
""")
            f.flush()
            try:
                names = extract_test_names(f.name)
                assert "test_foo" in names
                assert "test_bar" in names
                assert "helper" not in names
            finally:
                os.unlink(f.name)

    def test_extract_test_class_methods(self):
        """Test extracting test methods inside classes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
class TestMyModule:
    def test_something(self):
        pass

    def test_another(self):
        pass

    def helper(self):
        pass
""")
            f.flush()
            try:
                names = extract_test_names(f.name)
                assert "test_something" in names
                assert "test_another" in names
                assert "helper" not in names
            finally:
                os.unlink(f.name)

    def test_missing_file(self):
        """Test handling of missing test file."""
        names = extract_test_names("/nonexistent/test.py")
        assert names == []

    def test_syntax_error(self):
        """Test graceful handling of syntax errors."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test_broken(: pass")
            f.flush()
            try:
                names = extract_test_names(f.name)
                assert names == []
            finally:
                os.unlink(f.name)


class TestExtractTestScenarios:
    """Tests for extract_test_scenarios function."""

    def test_extract_list_item_scenarios(self):
        """Test extracting scenarios from list items."""
        body = """
# Overview

Some text

## Test Scenarios

- extract code symbols returns top-level functions
- extract code symbols returns class names
- extract code symbols does not return nested functions

## Next Section

Other content
"""
        scenarios = extract_test_scenarios(body)
        assert "extract code symbols returns top-level functions" in scenarios
        assert "extract code symbols returns class names" in scenarios
        assert "extract code symbols does not return nested functions" in scenarios

    def test_extract_subheading_scenarios(self):
        """Test extracting scenarios from ### sub-headings."""
        body = """
## Test Scenarios

### Scenario one
### Scenario two

## Next Section
"""
        scenarios = extract_test_scenarios(body)
        assert "Scenario one" in scenarios
        assert "Scenario two" in scenarios

    def test_no_test_scenarios_section(self):
        """Test handling when no Test Scenarios section exists."""
        body = """
# Overview

Some text

## Other Section

Content
"""
        scenarios = extract_test_scenarios(body)
        assert scenarios == []

    def test_mixed_list_and_headings(self):
        """Test extracting both list items and sub-headings."""
        body = """
## Test Scenarios

- First scenario
- Second scenario

### Third scenario

## Next
"""
        scenarios = extract_test_scenarios(body)
        assert "First scenario" in scenarios
        assert "Second scenario" in scenarios
        assert "Third scenario" in scenarios

    def test_case_insensitive_heading(self):
        """Test that heading matching is case-insensitive."""
        body = """
## test scenarios

- First item

## Next
"""
        scenarios = extract_test_scenarios(body)
        assert "First item" in scenarios

    def test_single_hash_heading(self):
        """Test that # Test Scenarios is recognized."""
        body = """
# Test Scenarios

- Scenario one

## Next
"""
        scenarios = extract_test_scenarios(body)
        assert "Scenario one" in scenarios


class TestExtractSpecSymbols:
    """Tests for extract_spec_symbols function."""

    def test_bundle_spec_with_functions_and_types(self):
        """Test extracting symbols from a bundle spec."""
        from dataclasses import dataclass, field
        from typing import Dict, Any

        @dataclass
        class MockMetadata:
            name: str = "test_bundle"
            type: str = "bundle"

        @dataclass
        class MockParsedSpec:
            metadata: Any
            body: str = ""
            bundle_functions: Dict = field(default_factory=dict)
            bundle_types: Dict = field(default_factory=dict)

        spec = MockParsedSpec(
            metadata=MockMetadata(),
            bundle_functions={"foo_func": None, "bar_func": None},
            bundle_types={"FooType": None, "BarType": None},
        )

        symbols = extract_spec_symbols(spec)
        assert "foo_func" in symbols
        assert "bar_func" in symbols
        assert "FooType" in symbols
        assert "BarType" in symbols

    def test_function_spec_returns_spec_name(self):
        """Test that function spec returns the spec name."""
        from dataclasses import dataclass, field
        from typing import Any

        @dataclass
        class MockMetadata:
            name: str = "my_function"
            type: str = "function"

        @dataclass
        class MockParsedSpec:
            metadata: Any
            body: str = ""
            bundle_functions: dict = field(default_factory=dict)
            bundle_types: dict = field(default_factory=dict)

        spec = MockParsedSpec(metadata=MockMetadata())
        symbols = extract_spec_symbols(spec)
        assert symbols == ["my_function"]

    def test_reference_spec_returns_empty(self):
        """Test that reference specs return empty list."""
        from dataclasses import dataclass, field
        from typing import Any, Dict

        @dataclass
        class MockMetadata:
            name: str = "external_lib"
            type: str = "reference"

        @dataclass
        class MockParsedSpec:
            metadata: Any
            body: str = ""
            bundle_functions: Dict = field(default_factory=dict)
            bundle_types: Dict = field(default_factory=dict)

        spec = MockParsedSpec(metadata=MockMetadata())
        symbols = extract_spec_symbols(spec)
        assert symbols == []

    def test_module_spec_scans_headings(self):
        """Test that module specs scan headings."""
        from dataclasses import dataclass, field
        from typing import Dict, Any

        @dataclass
        class MockMetadata:
            name: str = "my_module"
            type: str = "module"

        @dataclass
        class MockParsedSpec:
            metadata: Any
            body: str = """
# Overview

Description

## extract_symbols(parsed_spec) -> list of string

Function description

## format_output(data)

Another function

# Examples

Some examples
"""
            bundle_functions: Dict = field(default_factory=dict)
            bundle_types: Dict = field(default_factory=dict)

        spec = MockParsedSpec(metadata=MockMetadata())
        symbols = extract_spec_symbols(spec)
        # Should find headings that look like functions/classes
        assert any("extract" in s.lower() for s in symbols)


class TestFormatResultText:
    """Tests for format_result_text function."""

    def test_no_issues(self):
        """Test formatting result with no issues."""
        result = SpecDiffResult(spec_name="parser")
        text = format_result_text(result)
        assert "parser — no issues" in text

    def test_missing_issue(self):
        """Test formatting with MISSING issue."""
        result = SpecDiffResult(spec_name="parser")
        result.issues.append(
            SpecDiffIssue("MISSING", "extract_schema", "symbol missing")
        )
        text = format_result_text(result)
        assert "MISSING" in text
        assert "extract_schema" in text

    def test_undocumented_issue(self):
        """Test formatting with UNDOCUMENTED issue."""
        result = SpecDiffResult(spec_name="parser")
        result.issues.append(
            SpecDiffIssue("UNDOCUMENTED", "_private_func", "not declared")
        )
        text = format_result_text(result)
        assert "UNDOCUMENTED" in text
        assert "_private_func" in text

    def test_test_gap_issue(self):
        """Test formatting with TEST_GAP issue."""
        result = SpecDiffResult(spec_name="parser")
        result.issues.append(
            SpecDiffIssue("TEST_GAP", '"extract symbols"', "scenario not covered")
        )
        text = format_result_text(result)
        assert "TEST GAP" in text
        assert "extract symbols" in text


class TestFormatResultJson:
    """Tests for format_result_json function."""

    def test_json_formatting(self):
        """Test JSON formatting produces valid JSON."""
        result = SpecDiffResult(spec_name="parser", code_path="/path/to/parser.py")
        result.issues.append(
            SpecDiffIssue("MISSING", "extract_schema", "not found")
        )

        json_str = format_result_json(result)
        data = json.loads(json_str)

        assert data["spec_name"] == "parser"
        assert data["code_path"] == "/path/to/parser.py"
        assert data["issue_count"] == 1
        assert len(data["issues"]) == 1
        assert data["issues"][0]["kind"] == "MISSING"

    def test_json_parseable(self):
        """Test that output is valid parseable JSON."""
        result = SpecDiffResult(spec_name="test")
        result.issues.append(SpecDiffIssue("UNDOCUMENTED", "foo", "detail"))

        json_str = format_result_json(result)
        # Should not raise
        json.loads(json_str)


class TestDiffSpec:
    """Tests for diff_spec function."""

    def test_spec_file_not_found(self):
        """Test when spec file is not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = diff_spec("nonexistent", tmpdir)
            assert result.spec_name == "nonexistent"
            assert len(result.issues) == 1
            assert result.issues[0].kind == "MISSING"

    def test_no_issues_when_in_sync(self):
        """Test that diff_spec reports no issues when spec and code are in sync."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create spec directory and file
            spec_dir = os.path.join(tmpdir, "score")
            os.makedirs(spec_dir, exist_ok=True)

            spec_content = """---
name: test_module
type: bundle
---

# Overview

Test module

# Functions

```yaml:functions
my_function:
  inputs: {x: integer}
  outputs: {result: integer}
  behavior: "Test function"
```
"""
            spec_path = os.path.join(spec_dir, "test_module.spec.md")
            with open(spec_path, "w") as f:
                f.write(spec_content)

            # Create matching code file
            code_dir = os.path.join(tmpdir, "src", "specsoloist")
            os.makedirs(code_dir, exist_ok=True)
            code_path = os.path.join(code_dir, "test_module.py")
            with open(code_path, "w") as f:
                f.write("def my_function(x):\n    return x\n")

            result = diff_spec("test_module", tmpdir)
            assert result.issue_count == 0

    def test_missing_symbol_detection(self):
        """Test detection of MISSING symbols."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create spec
            spec_dir = os.path.join(tmpdir, "score")
            os.makedirs(spec_dir, exist_ok=True)
            spec_path = os.path.join(spec_dir, "test_module.spec.md")
            with open(spec_path, "w") as f:
                f.write("""---
name: test_module
type: bundle
---

# Overview

Test

# Functions

```yaml:functions
declared_func:
  inputs: {}
  outputs: {}
  behavior: "Test"
```
""")

            # Create code with missing function
            code_dir = os.path.join(tmpdir, "src", "specsoloist")
            os.makedirs(code_dir, exist_ok=True)
            code_path = os.path.join(code_dir, "test_module.py")
            with open(code_path, "w") as f:
                f.write("def other_func():\n    pass\n")

            result = diff_spec("test_module", tmpdir)
            missing = [i for i in result.issues if i.kind == "MISSING"]
            assert len(missing) > 0

    def test_undocumented_symbol_detection(self):
        """Test detection of UNDOCUMENTED symbols."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create spec
            spec_dir = os.path.join(tmpdir, "score")
            os.makedirs(spec_dir, exist_ok=True)
            spec_path = os.path.join(spec_dir, "test_module.spec.md")
            with open(spec_path, "w") as f:
                f.write("""---
name: test_module
type: function
---

# Overview

Test

# Interface

```yaml:schema
inputs: {}
outputs: {}
```

# Behavior

- Test behavior
""")

            # Create code with extra public function
            code_dir = os.path.join(tmpdir, "src", "specsoloist")
            os.makedirs(code_dir, exist_ok=True)
            code_path = os.path.join(code_dir, "test_module.py")
            with open(code_path, "w") as f:
                f.write("""
def test_module():
    pass

def extra_function():
    pass
""")

            result = diff_spec("test_module", tmpdir)
            undoc = [i for i in result.issues if i.kind == "UNDOCUMENTED"]
            assert len(undoc) > 0
            assert any("extra_function" in i.symbol for i in undoc)

    def test_private_symbols_not_flagged(self):
        """Test that private symbols are not flagged as UNDOCUMENTED."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal spec
            spec_dir = os.path.join(tmpdir, "score")
            os.makedirs(spec_dir, exist_ok=True)
            spec_path = os.path.join(spec_dir, "test_module.spec.md")
            with open(spec_path, "w") as f:
                f.write("""---
name: test_module
type: function
---

# Overview

Test

# Interface

```yaml:schema
inputs: {}
outputs: {}
```

# Behavior

- Test
""")

            # Create code with private function
            code_dir = os.path.join(tmpdir, "src", "specsoloist")
            os.makedirs(code_dir, exist_ok=True)
            code_path = os.path.join(code_dir, "test_module.py")
            with open(code_path, "w") as f:
                f.write("""
def test_module():
    pass

def _private_helper():
    pass
""")

            result = diff_spec("test_module", tmpdir)
            undoc = [i for i in result.issues if i.kind == "UNDOCUMENTED"]
            # _private_helper should not be flagged
            assert not any("_private_helper" in i.symbol for i in undoc)


class TestScenarioMatching:
    """Integration tests for test scenario matching."""

    def test_scenario_matches_test_by_word(self):
        """Test that scenario matching works by significant word matching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create spec with test scenario
            spec_dir = os.path.join(tmpdir, "score")
            os.makedirs(spec_dir, exist_ok=True)
            spec_path = os.path.join(spec_dir, "test_module.spec.md")
            with open(spec_path, "w") as f:
                f.write("""---
name: test_module
type: function
---

# Overview

Test

# Interface

```yaml:schema
inputs: {}
outputs: {}
```

# Behavior

- Test

# Test Scenarios

- extract code symbols returns top-level functions

# Examples

Example
""")

            # Create test file with matching test
            test_dir = os.path.join(tmpdir, "tests")
            os.makedirs(test_dir, exist_ok=True)
            test_path = os.path.join(test_dir, "test_test_module.py")
            with open(test_path, "w") as f:
                f.write("""
def test_extract_symbols():
    pass
""")

            # Create minimal code file
            code_dir = os.path.join(tmpdir, "src", "specsoloist")
            os.makedirs(code_dir, exist_ok=True)
            code_path = os.path.join(code_dir, "test_module.py")
            with open(code_path, "w") as f:
                f.write("def test_module():\n    pass\n")

            result = diff_spec("test_module", tmpdir)
            gaps = [i for i in result.issues if i.kind == "TEST_GAP"]
            # "extract code symbols" should match "test_extract_symbols"
            assert len(gaps) == 0
