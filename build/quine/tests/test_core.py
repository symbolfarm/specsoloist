"""Tests for SpecSoloistCore orchestrator."""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import with alias to avoid pytest collection issues
from specsoloist.core import SpecSoloistCore as Core
from specsoloist.core import BuildResult
from specsoloist.config import SpecSoloistConfig, LanguageConfig
from specsoloist.parser import SpecParser, ParsedSpec, SpecMetadata
from specsoloist.compiler import SpecCompiler
from specsoloist.runner import TestRunner, TestResult
from specsoloist.resolver import DependencyResolver, DependencyGraph
from specsoloist.manifest import BuildManifest, SpecBuildInfo


class TestBuildResult:
    """Test the BuildResult dataclass."""

    def test_build_result_creation(self):
        """Test creating a BuildResult."""
        result = BuildResult(
            success=True,
            specs_compiled=["spec1", "spec2"],
            specs_skipped=["spec3"],
            specs_failed=[],
            build_order=["spec1", "spec2", "spec3"],
            errors={}
        )
        assert result.success is True
        assert result.specs_compiled == ["spec1", "spec2"]
        assert result.specs_skipped == ["spec3"]
        assert result.specs_failed == []
        assert len(result.errors) == 0

    def test_build_result_with_errors(self):
        """Test BuildResult with compilation errors."""
        errors = {"spec1": "Failed to compile"}
        result = BuildResult(
            success=False,
            specs_compiled=[],
            specs_skipped=[],
            specs_failed=["spec1"],
            build_order=["spec1"],
            errors=errors
        )
        assert result.success is False
        assert result.errors["spec1"] == "Failed to compile"


class TestSpecSoloistCoreInitialization:
    """Test SpecSoloistCore initialization."""

    def test_init_with_default_root_dir(self):
        """Test initialization with default root directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            assert core.root_dir == os.path.abspath(tmpdir)
            assert core.config is not None
            assert core.parser is not None
            assert core.runner is not None
            assert core.resolver is not None

    def test_init_creates_directories(self):
        """Test that initialization creates necessary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(
                root_dir=tmpdir,
                src_dir="specs",
                build_dir="out"
            )
            core = Core(root_dir=tmpdir, config=config)

            assert os.path.exists(os.path.join(tmpdir, "specs"))
            assert os.path.exists(os.path.join(tmpdir, "out"))

    def test_init_with_api_key(self):
        """Test initialization with explicit API key (deprecated parameter)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # When config is provided, api_key parameter is ignored (deprecated)
            config = SpecSoloistConfig(root_dir=tmpdir, api_key="configured-key")
            core = Core(root_dir=tmpdir, api_key="test-key", config=config)
            # Config API key takes precedence
            assert core.api_key == "configured-key"

            # But if no config is provided, api_key parameter is used
            core2 = Core(root_dir=tmpdir, api_key="test-key")
            assert core2.api_key == "test-key"

    def test_init_exposes_public_attributes(self):
        """Test that public attributes are exposed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            assert hasattr(core, 'project_dir') or hasattr(core, 'root_dir')
            assert hasattr(core, 'config')
            assert hasattr(core, 'parser')
            assert hasattr(core, 'runner')
            assert hasattr(core, 'resolver')


class TestSpecManagement:
    """Test spec management methods."""

    def test_list_specs(self):
        """Test listing available specs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            # Create some specs
            with open(os.path.join(config.src_path, "test1.spec.md"), "w") as f:
                f.write("---\nname: test1\n---\n# Overview\nTest spec.")
            with open(os.path.join(config.src_path, "test2.spec.md"), "w") as f:
                f.write("---\nname: test2\n---\n# Overview\nAnother spec.")

            specs = core.list_specs()
            assert "test1.spec.md" in specs or "test1" in specs
            assert "test2.spec.md" in specs or "test2" in specs

    def test_read_spec(self):
        """Test reading a spec file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec_content = "---\nname: test\n---\n# Overview\nTest spec."
            spec_path = os.path.join(config.src_path, "test.spec.md")
            with open(spec_path, "w") as f:
                f.write(spec_content)

            content = core.read_spec("test")
            assert "name: test" in content
            assert "Test spec" in content

    def test_create_spec(self):
        """Test creating a new spec."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            result = core.create_spec("newspec", "A new specification", type="function")
            assert "Created spec" in result
            assert os.path.exists(os.path.join(config.src_path, "newspec.spec.md"))

    def test_validate_spec_valid(self):
        """Test validating a well-formed spec."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec_content = """---
name: test
type: function
---
# Overview
A test function.

# Interface

```yaml:schema
inputs:
  x:
    type: int
outputs:
  y:
    type: int
```

# Behavior
Returns x + 1.
"""
            spec_path = os.path.join(config.src_path, "test.spec.md")
            with open(spec_path, "w") as f:
                f.write(spec_content)

            result = core.validate_spec("test")
            assert result["valid"] is True

    def test_validate_spec_invalid(self):
        """Test validating an invalid spec."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec_content = "---\nname: test\n---\nNo required sections"
            spec_path = os.path.join(config.src_path, "test.spec.md")
            with open(spec_path, "w") as f:
                f.write(spec_content)

            result = core.validate_spec("test")
            assert result["valid"] is False
            assert len(result["errors"]) > 0


class TestCompilation:
    """Test compilation methods."""

    def test_compile_spec_dispatches_typedef(self):
        """Test that typedef specs use compile_typedef."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            # Create a valid function spec (typedef validation requires function-style sections)
            spec_content = """---
name: mytype
type: typedef
---
# Overview
A custom type.

# Interface

```yaml:schema
inputs: {}
outputs: {}
```

# Behavior
Defines a custom type.
"""
            spec_path = os.path.join(config.src_path, "mytype.spec.md")
            with open(spec_path, "w") as f:
                f.write(spec_content)

            # Mock validation to return valid
            with patch.object(core, 'validate_spec') as mock_validate, \
                 patch.object(core.parser, 'parse_spec') as mock_parse, \
                 patch.object(core, '_get_compiler') as mock_get_compiler, \
                 patch.object(core.runner, 'write_code') as mock_write:

                mock_validate.return_value = {"valid": True, "errors": []}
                parsed = Mock()
                parsed.metadata.type = "typedef"
                parsed.metadata.dependencies = []
                parsed.metadata.language_target = None
                mock_parse.return_value = parsed

                mock_compiler = Mock()
                mock_compiler.compile_typedef.return_value = "class MyType: pass"
                mock_get_compiler.return_value = mock_compiler
                mock_write.return_value = "/path/to/mytype.py"

                result = core.compile_spec("mytype")
                mock_compiler.compile_typedef.assert_called()

    def test_compile_spec_reference_spec_no_code(self):
        """Test that reference specs return no code message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec_content = """---
name: reference_spec
type: reference
---
# Overview
Documentation only.

# API

External API documentation here.
"""
            spec_path = os.path.join(config.src_path, "reference_spec.spec.md")
            with open(spec_path, "w") as f:
                f.write(spec_content)

            result = core.compile_spec("reference_spec")
            assert "no code generated" in result or "Reference" in result

    def test_compile_tests_skips_typedef(self):
        """Test that compile_tests skips typedef specs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec_content = """---
name: mytype
type: typedef
---
# Overview
A custom type.
"""
            spec_path = os.path.join(config.src_path, "mytype.spec.md")
            with open(spec_path, "w") as f:
                f.write(spec_content)

            result = core.compile_tests("mytype")
            assert "Skipped" in result and "typedef" in result

    def test_compile_tests_reference_with_verification(self):
        """Test compile_tests for reference specs with verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec_content = """---
name: api_ref
type: reference
---
# Overview
External API docs.

# Verification

```python
import requests
resp = requests.get("https://api.example.com")
assert resp.status_code == 200
```
"""
            spec_path = os.path.join(config.src_path, "api_ref.spec.md")
            with open(spec_path, "w") as f:
                f.write(spec_content)

            result = core.compile_tests("api_ref")
            assert "Generated" in result or "tests" in result

    def test_compile_project_sequential(self):
        """Test sequential compilation of multiple specs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            # Create dependency: spec2 depends on spec1
            spec1_content = """---
name: spec1
type: function
---
# Overview
Base spec.

# Interface

```yaml:schema
inputs: {}
outputs:
  result:
    type: string
```

# Behavior
Returns "done".
"""
            spec2_content = """---
name: spec2
type: function
dependencies:
  - name: spec1
    from: spec1.spec.md
---
# Overview
Depends on spec1.

# Interface

```yaml:schema
inputs: {}
outputs:
  value:
    type: int
```

# Behavior
Uses spec1 and returns 42.
"""
            with open(os.path.join(config.src_path, "spec1.spec.md"), "w") as f:
                f.write(spec1_content)
            with open(os.path.join(config.src_path, "spec2.spec.md"), "w") as f:
                f.write(spec2_content)

            # Mock compilation
            with patch.object(core, 'compile_spec') as mock_compile, \
                 patch.object(core, 'compile_tests') as mock_tests:
                mock_compile.return_value = "Code compiled"
                mock_tests.return_value = "Tests compiled"

                result = core.compile_project(specs=["spec1", "spec2"], generate_tests=False)

                # Check build order: spec1 before spec2
                assert result.build_order == ["spec1", "spec2"]
                assert result.success is True

    def test_get_build_order(self):
        """Test getting build order without compilation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            # Create specs with dependencies
            spec1 = "---\nname: base\n---\n# Overview\nBase."
            spec2 = "---\nname: derived\ndependencies:\n  - name: base\n    from: base.spec.md\n---\n# Overview\nDerived."

            with open(os.path.join(config.src_path, "base.spec.md"), "w") as f:
                f.write(spec1)
            with open(os.path.join(config.src_path, "derived.spec.md"), "w") as f:
                f.write(spec2)

            order = core.get_build_order()
            assert "base" in order
            assert "derived" in order
            assert order.index("base") < order.index("derived")


class TestBuildOrder:
    """Test dependency resolution and build order."""

    def test_get_dependency_graph(self):
        """Test getting the dependency graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec1 = "---\nname: a\n---\n# Overview\nA."
            spec2 = "---\nname: b\ndependencies:\n  - a\n---\n# Overview\nB depends on A."

            with open(os.path.join(config.src_path, "a.spec.md"), "w") as f:
                f.write(spec1)
            with open(os.path.join(config.src_path, "b.spec.md"), "w") as f:
                f.write(spec2)

            graph = core.get_dependency_graph()
            assert isinstance(graph, DependencyGraph)


class TestTesting:
    """Test testing methods."""

    def test_run_tests(self):
        """Test running tests for a spec."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec_content = """---
name: test_spec
type: function
---
# Overview
A test spec.

# Interface

```yaml:schema
inputs: {}
outputs:
  x:
    type: int
```

# Behavior
Returns 1.
"""
            spec_path = os.path.join(config.src_path, "test_spec.spec.md")
            with open(spec_path, "w") as f:
                f.write(spec_content)

            # Mock the runner
            with patch.object(core.runner, 'run_tests') as mock_run:
                mock_run.return_value = TestResult(success=True, output="All passed", return_code=0)

                result = core.run_tests("test_spec")
                assert result["success"] is True
                assert "All passed" in result["output"]

    def test_run_tests_reference_spec_no_verification(self):
        """Test running tests for reference spec without verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec_content = """---
name: ref_spec
type: reference
---
# Overview
Reference documentation.
"""
            spec_path = os.path.join(config.src_path, "ref_spec.spec.md")
            with open(spec_path, "w") as f:
                f.write(spec_content)

            result = core.run_tests("ref_spec")
            assert result["success"] is True
            assert "reference" in result["output"].lower()

    def test_run_all_tests(self):
        """Test running all tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec1 = """---
name: spec1
type: function
---
# Overview
Spec 1.

# Interface

```yaml:schema
inputs: {}
outputs:
  x:
    type: int
```

# Behavior
Returns 1.
"""
            spec2 = """---
name: spec2
type: typedef
---
# Overview
A type.

# Schema

```yaml:schema
inputs: {}
outputs: {}
```
"""
            with open(os.path.join(config.src_path, "spec1.spec.md"), "w") as f:
                f.write(spec1)
            with open(os.path.join(config.src_path, "spec2.spec.md"), "w") as f:
                f.write(spec2)

            # Mock the test runner
            with patch.object(core.runner, 'test_exists') as mock_exists, \
                 patch.object(core.runner, 'run_tests') as mock_run:
                mock_exists.return_value = True
                mock_run.return_value = TestResult(success=True, output="Pass", return_code=0)

                with patch.object(core, 'run_tests') as mock_run_tests:
                    mock_run_tests.return_value = {"success": True, "output": "Pass"}

                    result = core.run_all_tests()
                    assert "results" in result


class TestSelfHealing:
    """Test self-healing fix loop."""

    def test_attempt_fix_no_error(self):
        """Test attempt_fix when tests already pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec_content = """---
name: passing_spec
type: function
---
# Overview
A spec.

# Interface

```yaml:schema
inputs: {}
outputs:
  x:
    type: int
```

# Behavior
Returns 1.
"""
            spec_path = os.path.join(config.src_path, "passing_spec.spec.md")
            with open(spec_path, "w") as f:
                f.write(spec_content)

            with patch.object(core.runner, 'run_tests') as mock_run:
                mock_run.return_value = TestResult(success=True, output="Pass", return_code=0)

                result = core.attempt_fix("passing_spec")
                assert "already passed" in result.lower()

    def test_attempt_fix_with_error(self):
        """Test attempt_fix with failing tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec_content = """---
name: failing_spec
type: function
---
# Overview
A failing spec.

# Interface

```yaml:schema
inputs: {}
outputs:
  x:
    type: int
```

# Behavior
Returns x.
"""
            spec_path = os.path.join(config.src_path, "failing_spec.spec.md")
            with open(spec_path, "w") as f:
                f.write(spec_content)

            code = "def foo():\n    return None"
            test_code = "def test_foo():\n    assert foo() == 1"

            with patch.object(core.runner, 'run_tests') as mock_run, \
                 patch.object(core.runner, 'read_code') as mock_read_code, \
                 patch.object(core.runner, 'read_tests') as mock_read_tests, \
                 patch.object(core, '_get_compiler') as mock_get_compiler:

                mock_run.return_value = TestResult(
                    success=False,
                    output="AssertionError: None != 1",
                    return_code=1
                )
                mock_read_code.return_value = code
                mock_read_tests.return_value = test_code

                mock_compiler = Mock()
                mock_compiler.generate_fix.return_value = "### FILE: test\n### END"
                mock_compiler.parse_fix_response.return_value = {}
                mock_get_compiler.return_value = mock_compiler

                result = core.attempt_fix("failing_spec")
                mock_compiler.generate_fix.assert_called()


class TestVerification:
    """Test project verification."""

    def test_verify_project_valid(self):
        """Test verifying a valid project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec_content = """---
name: valid
type: function
---
# Overview
A valid spec.

# Interface

```yaml:schema
inputs: {}
outputs:
  x:
    type: int
```

# Behavior
Returns 1.
"""
            with open(os.path.join(config.src_path, "valid.spec.md"), "w") as f:
                f.write(spec_content)

            result = core.verify_project()
            assert "results" in result
            assert "success" in result

    def test_verify_project_circular_dependency(self):
        """Test verification detects circular dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            spec_a = """---
name: a
dependencies:
  - b
---
# Overview
Depends on B.
"""
            spec_b = """---
name: b
dependencies:
  - a
---
# Overview
Depends on A.
"""
            with open(os.path.join(config.src_path, "a.spec.md"), "w") as f:
                f.write(spec_a)
            with open(os.path.join(config.src_path, "b.spec.md"), "w") as f:
                f.write(spec_b)

            result = core.verify_project()
            # Should detect the circular dependency error
            assert result["success"] is False or "error" in result


class TestLazyLoading:
    """Test lazy initialization of components."""

    def test_compiler_lazy_loading(self):
        """Test that compiler is created lazily."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            # Initially should be None
            assert core._compiler is None

            # Calling _get_compiler creates it
            with patch.object(config, 'create_provider') as mock_provider:
                mock_provider.return_value = Mock()
                compiler = core._get_compiler()
                assert compiler is not None
                assert core._compiler is not None

    def test_manifest_lazy_loading(self):
        """Test that manifest is loaded lazily."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            core = Core(root_dir=tmpdir, config=config)

            # Initially should be None
            assert core._manifest is None

            # Calling _get_manifest loads it
            manifest = core._get_manifest()
            assert manifest is not None
            assert core._manifest is not None
