"""
Tests for the `type: reference` spec type.

Covers:
- Parser: valid reference spec, missing # API is an error, missing # Verification is a warning
- Compiler: _build_import_context injects full body for reference deps, import lines for normal deps
- Core: reference spec skips code generation, generates verification tests, synthetic pass for no-verification
"""

import os
import tempfile
import shutil
import pytest

from specsoloist.parser import SpecParser
from specsoloist.compiler import SpecCompiler
from specsoloist.core import SpecSoloistCore
from specsoloist.config import SpecSoloistConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_REFERENCE_SPEC = """\
---
name: mylib_interface
type: reference
status: stable
---

# Overview

MyLib (`mylib >= 1.0`) is a fictional library used for testing.

# API

## do_thing()

Returns 42.

# Verification

```python
import mylib
assert mylib.do_thing() == 42
```
"""

REFERENCE_MISSING_API = """\
---
name: mylib_interface
type: reference
---

# Overview

MyLib is a fictional library.
"""

REFERENCE_MISSING_VERIFICATION = """\
---
name: mylib_interface
type: reference
---

# Overview

MyLib (`mylib >= 1.0`) is a fictional library.

# API

## do_thing()

Returns 42.
"""


def _write_spec(tmp_dir: str, name: str, content: str) -> None:
    path = os.path.join(tmp_dir, f"{name}.spec.md")
    os.makedirs(tmp_dir, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestReferenceParser:
    def test_valid_reference_spec_parses(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_spec(tmp, "mylib_interface", VALID_REFERENCE_SPEC)
            parser = SpecParser(tmp)
            parsed = parser.parse_spec("mylib_interface")
            assert parsed.metadata.type == "reference"
            assert parsed.metadata.name == "mylib_interface"
            # No schema/functions/steps extracted for reference specs
            assert parsed.schema is None
            assert parsed.bundle_functions == {}
            assert parsed.steps == []

    def test_valid_reference_spec_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_spec(tmp, "mylib_interface", VALID_REFERENCE_SPEC)
            parser = SpecParser(tmp)
            result = parser.validate_spec("mylib_interface")
            assert result["valid"] is True
            assert result["errors"] == []

    def test_missing_api_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_spec(tmp, "mylib_interface", REFERENCE_MISSING_API)
            parser = SpecParser(tmp)
            result = parser.validate_spec("mylib_interface")
            assert result["valid"] is False
            assert any("# API" in e for e in result["errors"])

    def test_missing_overview_is_error(self):
        content = """\
---
name: mylib_interface
type: reference
---

# API

## do_thing()

Returns 42.
"""
        with tempfile.TemporaryDirectory() as tmp:
            _write_spec(tmp, "mylib_interface", content)
            parser = SpecParser(tmp)
            result = parser.validate_spec("mylib_interface")
            assert result["valid"] is False
            assert any("# Overview" in e for e in result["errors"])

    def test_missing_verification_is_warning_not_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_spec(tmp, "mylib_interface", REFERENCE_MISSING_VERIFICATION)
            parser = SpecParser(tmp)
            # validate_spec should pass (valid)
            result = parser.validate_spec("mylib_interface")
            assert result["valid"] is True
            # get_reference_warnings should include verification warning
            parsed = parser.parse_spec("mylib_interface")
            warnings = parser.get_reference_warnings(parsed)
            assert any("Verification" in w for w in warnings)

    def test_extract_verification_snippet(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_spec(tmp, "mylib_interface", VALID_REFERENCE_SPEC)
            parser = SpecParser(tmp)
            parsed = parser.parse_spec("mylib_interface")
            snippet = parser.extract_verification_snippet(parsed.body)
            assert "import mylib" in snippet
            assert "mylib.do_thing() == 42" in snippet

    def test_extract_verification_snippet_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write_spec(tmp, "mylib_interface", REFERENCE_MISSING_VERIFICATION)
            parser = SpecParser(tmp)
            parsed = parser.parse_spec("mylib_interface")
            snippet = parser.extract_verification_snippet(parsed.body)
            assert snippet == ""

    def test_no_version_range_triggers_warning(self):
        content = """\
---
name: mylib_interface
type: reference
---

# Overview

MyLib is a fictional library (no version range here).

# API

## do_thing()

Returns 42.
"""
        with tempfile.TemporaryDirectory() as tmp:
            _write_spec(tmp, "mylib_interface", content)
            parser = SpecParser(tmp)
            parsed = parser.parse_spec("mylib_interface")
            warnings = parser.get_reference_warnings(parsed)
            assert any("version" in w.lower() for w in warnings)


# ---------------------------------------------------------------------------
# Compiler tests
# ---------------------------------------------------------------------------

class MockProvider:
    def __init__(self):
        self.calls = []

    def generate(self, prompt: str, temperature: float = 0.1, model=None) -> str:
        self.calls.append(prompt)
        return "# mock code"


class TestReferenceCompilerInjection:
    def _make_compiler(self):
        return SpecCompiler(provider=MockProvider(), global_context="")

    def test_reference_dep_injects_full_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref_content = """\
---
name: mylib_interface
type: reference
---

# Overview

MyLib >= 1.0

# API

## do_thing()

Returns 42.
"""
            regular_content = """\
---
name: myapp
type: bundle
dependencies:
  - mylib_interface
---

# Overview

App using mylib.

# Functions

```yaml:functions
run:
  inputs: {}
  outputs: {result: {type: integer}}
  behavior: "Run the app"
```
"""
            _write_spec(tmp, "mylib_interface", ref_content)
            _write_spec(tmp, "myapp", regular_content)
            parser = SpecParser(tmp)
            ref_spec = parser.parse_spec("mylib_interface")
            app_spec = parser.parse_spec("myapp")

            compiler = self._make_compiler()
            reference_specs = {"mylib_interface": ref_spec}
            ctx = compiler._build_import_context(app_spec, reference_specs=reference_specs)

            # Should contain the reference spec body, not just an import line
            assert "## Reference: mylib_interface" in ctx
            assert "do_thing()" in ctx
            # Should NOT emit a plain import line for the reference dep
            assert "Import from `mylib_interface`" not in ctx

    def test_regular_dep_emits_import_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            regular_content = """\
---
name: myapp
type: bundle
dependencies:
  - utils
---

# Overview

App using utils.

# Functions

```yaml:functions
run:
  inputs: {}
  outputs: {result: {type: integer}}
  behavior: "Run the app"
```
"""
            _write_spec(tmp, "myapp", regular_content)
            parser = SpecParser(tmp)
            app_spec = parser.parse_spec("myapp")

            compiler = self._make_compiler()
            ctx = compiler._build_import_context(app_spec, reference_specs={})

            assert "Import from `utils`" in ctx

    def test_mixed_deps_reference_and_regular(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref_content = """\
---
name: mylib_interface
type: reference
---

# Overview

MyLib >= 1.0

# API

## do_thing()
"""
            app_content = """\
---
name: myapp
type: bundle
dependencies:
  - mylib_interface
  - utils
---

# Overview

App.

# Functions

```yaml:functions
run:
  inputs: {}
  outputs: {result: {type: integer}}
  behavior: "Run"
```
"""
            _write_spec(tmp, "mylib_interface", ref_content)
            _write_spec(tmp, "myapp", app_content)
            parser = SpecParser(tmp)
            ref_spec = parser.parse_spec("mylib_interface")
            app_spec = parser.parse_spec("myapp")

            compiler = self._make_compiler()
            ctx = compiler._build_import_context(app_spec, reference_specs={"mylib_interface": ref_spec})

            assert "## Reference: mylib_interface" in ctx
            assert "Import from `utils`" in ctx


# ---------------------------------------------------------------------------
# Core tests
# ---------------------------------------------------------------------------

@pytest.fixture
def test_env():
    env_dir = "test_env_reference"
    if os.path.exists(env_dir):
        shutil.rmtree(env_dir)
    os.makedirs(env_dir)
    yield env_dir
    if os.path.exists(env_dir):
        shutil.rmtree(env_dir)


class TestReferenceCore:
    def _make_core(self, env_dir: str) -> SpecSoloistCore:
        return SpecSoloistCore(env_dir)

    def test_compile_spec_skips_reference(self, test_env):
        src_dir = os.path.join(test_env, "src")
        os.makedirs(src_dir, exist_ok=True)
        _write_spec(src_dir, "mylib_interface", VALID_REFERENCE_SPEC)
        core = self._make_core(test_env)
        result = core.compile_spec("mylib_interface")
        assert "Reference spec" in result
        assert "no code generated" in result
        # No implementation file should exist
        build_dir = os.path.join(test_env, "build")
        impl_path = os.path.join(build_dir, "mylib_interface.py")
        assert not os.path.exists(impl_path)

    def test_compile_tests_generates_verification_file(self, test_env):
        src_dir = os.path.join(test_env, "src")
        os.makedirs(src_dir, exist_ok=True)
        _write_spec(src_dir, "mylib_interface", VALID_REFERENCE_SPEC)
        core = self._make_core(test_env)
        result = core.compile_tests("mylib_interface")
        assert "verification" in result.lower() or "Generated" in result
        # Test file should exist
        build_dir = os.path.join(test_env, "build")
        test_path = os.path.join(build_dir, "test_mylib_interface.py")
        assert os.path.exists(test_path)
        content = open(test_path).read()
        assert "def test_verify" in content
        assert "import mylib" in content

    def test_compile_tests_no_verification_skips(self, test_env):
        src_dir = os.path.join(test_env, "src")
        os.makedirs(src_dir, exist_ok=True)
        _write_spec(src_dir, "mylib_interface", REFERENCE_MISSING_VERIFICATION)
        core = self._make_core(test_env)
        result = core.compile_tests("mylib_interface")
        assert "Skipped" in result
        # No test file should exist
        build_dir = os.path.join(test_env, "build")
        test_path = os.path.join(build_dir, "test_mylib_interface.py")
        assert not os.path.exists(test_path)

    def test_run_tests_synthetic_pass_for_no_verification(self, test_env):
        src_dir = os.path.join(test_env, "src")
        os.makedirs(src_dir, exist_ok=True)
        _write_spec(src_dir, "mylib_interface", REFERENCE_MISSING_VERIFICATION)
        core = self._make_core(test_env)
        result = core.run_tests("mylib_interface")
        assert result["success"] is True
        assert "No verification" in result["output"] or "reference" in result["output"].lower()
