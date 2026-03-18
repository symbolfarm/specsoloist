"""Tests for the core module."""

import os
import pytest
from unittest.mock import MagicMock, patch

from specsoloist.config import SpecSoloistConfig
from specsoloist.core import BuildResult, SpecSoloistCore


SIMPLE_SPEC = """---
name: myspec
description: A simple spec
type: bundle
---

# Overview

A simple spec.

# Functions

```yaml:functions
greet:
  inputs:
    name: {type: string}
  outputs:
    message: {type: string}
  behavior: "Return a greeting"
```
"""

REFERENCE_SPEC = """---
name: myref
type: reference
---

# Overview

API documentation.

# Verification

```python
assert True
```
"""


@pytest.fixture
def spec_dir(tmp_path):
    (tmp_path / "myspec.spec.md").write_text(SIMPLE_SPEC)
    return tmp_path


@pytest.fixture
def mock_config(tmp_path):
    config = SpecSoloistConfig(
        root_dir=str(tmp_path),
        src_dir="specs",
        build_dir="build",
    )
    return config


@pytest.fixture
def core(tmp_path, spec_dir):
    config = SpecSoloistConfig(
        root_dir=str(tmp_path),
        src_dir=str(spec_dir),
        build_dir=str(tmp_path / "build"),
    )
    config.src_path = str(spec_dir)
    config.build_path = str(tmp_path / "build")
    os.makedirs(config.build_path, exist_ok=True)

    # Mock provider
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "def greet(name): return f'Hello {name}'"

    core = SpecSoloistCore.__new__(SpecSoloistCore)
    core.config = config
    core.project_dir = str(tmp_path)
    from specsoloist.parser import SpecParser
    from specsoloist.runner import TestRunner
    from specsoloist.resolver import DependencyResolver
    core.parser = SpecParser(str(spec_dir))
    core.runner = TestRunner(str(tmp_path / "build"), config=config)
    core.resolver = DependencyResolver(parser=core.parser)
    core._compiler = None
    core._manifest = None

    from specsoloist.compiler import SpecCompiler
    core._compiler = SpecCompiler(provider=mock_provider)

    return core


class TestBuildResult:
    def test_default_creation(self):
        result = BuildResult(success=True)
        assert result.success is True
        assert result.specs_compiled == []
        assert result.specs_failed == []
        assert result.specs_skipped == []
        assert result.errors == {}

    def test_with_data(self):
        result = BuildResult(
            success=False,
            specs_compiled=["a", "b"],
            specs_failed=["c"],
            errors={"c": "compilation error"},
        )
        assert not result.success
        assert "a" in result.specs_compiled
        assert "c" in result.specs_failed
        assert "c" in result.errors


class TestSpecSoloistCore:
    def test_list_specs(self, core):
        specs = core.list_specs()
        assert any("myspec" in s for s in specs)

    def test_read_spec(self, core):
        content = core.read_spec("myspec")
        assert "myspec" in content
        assert "# Overview" in content

    def test_validate_spec_valid(self, core):
        result = core.validate_spec("myspec")
        assert result["valid"] is True

    def test_validate_spec_missing(self, core):
        result = core.validate_spec("nonexistent")
        assert result["valid"] is False

    def test_get_build_order(self, core):
        order = core.get_build_order()
        assert "myspec" in order

    def test_compile_spec_returns_code(self, core):
        code = core.compile_spec("myspec")
        assert isinstance(code, str)
        assert len(code) > 0

    def test_compile_spec_writes_file(self, core):
        core.compile_spec("myspec")
        assert core.runner.code_exists("myspec")

    def test_compile_tests_writes_file(self, core):
        core.compile_tests("myspec")
        assert core.runner.test_exists("myspec")

    def test_compile_spec_reference_skipped(self, core, spec_dir):
        (spec_dir / "myref.spec.md").write_text(REFERENCE_SPEC)
        result = core.compile_spec("myref")
        assert "reference" in result.lower() or "skipped" in result.lower()

    def test_compile_tests_reference_verification(self, core, spec_dir):
        (spec_dir / "myref.spec.md").write_text(REFERENCE_SPEC)
        result = core.compile_tests("myref")
        # Should extract verification snippet
        assert isinstance(result, str)

    def test_run_tests_no_test_file(self, core):
        result = core.run_tests("myspec")
        assert result["success"] is False or "not found" in result["output"].lower()

    def test_run_all_tests(self, core):
        result = core.run_all_tests()
        assert "success" in result
        assert "results" in result

    def test_compile_project(self, core):
        result = core.compile_project(specs=["myspec"])
        assert isinstance(result, BuildResult)
        assert result.build_order == ["myspec"]

    def test_compile_project_success(self, core):
        result = core.compile_project(specs=["myspec"], generate_tests=False)
        assert "myspec" in result.specs_compiled

    def test_compile_project_failed_spec(self, core):
        # Make compiler raise an error
        core._compiler.compile_code = MagicMock(side_effect=Exception("LLM error"))
        result = core.compile_project(specs=["myspec"], generate_tests=False)
        assert "myspec" in result.specs_failed
        assert not result.success

    def test_get_dependency_graph(self, core):
        graph = core.get_dependency_graph()
        assert graph is not None

    def test_attempt_fix_no_tests(self, core):
        """attempt_fix when tests don't exist."""
        result = core.attempt_fix("myspec")
        # Should handle gracefully
        assert isinstance(result, str)

    def test_attempt_fix_passing_tests(self, core):
        """attempt_fix when tests already pass."""
        with patch.object(core.runner, 'run_tests') as mock_run:
            from specsoloist.runner import TestResult
            mock_run.return_value = TestResult(success=True, output="1 passed")
            result = core.attempt_fix("myspec")
            assert "passing" in result.lower() or "no fix" in result.lower()

    def test_verify_project(self, core):
        result = core.verify_project()
        assert "success" in result
        assert "results" in result
