"""
Tests for SpecParser.
"""

import os
import tempfile
from specsoloist.parser import SpecParser


def test_parse_metadata_with_description():
    """Test that description is parsed from frontmatter."""
    content = """---
name: test_component
description: A explicit description from frontmatter.
---
# 1. Overview
This should be ignored since frontmatter has it.
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")

        assert parsed.metadata.name == "test_component"
        assert parsed.metadata.description == "A explicit description from frontmatter."


def test_extract_description_from_overview():
    """Test that description is extracted from Overview if missing in frontmatter."""
    content = """---
name: test_component
---
# 1. Overview
This is the extracted description.

# 2. Interface
...
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")

        assert parsed.metadata.description == "This is the extracted description."


def test_extract_description_ignores_empty_lines():
    """Test that the first non-empty line after Overview is used."""
    content = """---
name: test_component
---
# 1. Overview


This is the real description.
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")

        assert parsed.metadata.description == "This is the real description."


def test_parse_tags():
    """Test that tags are parsed from frontmatter."""
    content = """---
name: test_component
type: function
tags:
  - math
  - pure
---
# Overview
A function.
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")

        assert parsed.metadata.tags == ["math", "pure"]


def test_parse_version():
    """Test that version is parsed from frontmatter."""
    content = """---
name: test_component
version: 1.2.3
---
# Overview
A versioned component.
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")

        assert parsed.metadata.version == "1.2.3"


def test_language_target_optional():
    """Test that language_target is optional and defaults to None."""
    content = """---
name: test_component
type: function
---
# Overview
A language-agnostic spec.
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")

        assert parsed.metadata.language_target is None


def test_parse_bundle_functions():
    """Test parsing of yaml:functions block in bundles."""
    content = """---
name: math_utils
type: bundle
---
# Overview
Math utilities.

# Functions
```yaml:functions
add:
  inputs: {a: integer, b: integer}
  outputs: {result: integer}
  behavior: Return a + b

subtract:
  inputs: {a: integer, b: integer}
  outputs: {result: integer}
  behavior: Return a - b
```
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")

        assert parsed.metadata.type == "bundle"
        assert "add" in parsed.bundle_functions
        assert "subtract" in parsed.bundle_functions
        assert parsed.bundle_functions["add"].behavior == "Return a + b"


def test_parse_bundle_types():
    """Test parsing of yaml:types block in bundles."""
    content = """---
name: types_bundle
type: bundle
---
# Overview
Common types.

# Types
```yaml:types
point:
  properties:
    x: {type: number}
    y: {type: number}
  required: [x, y]
```
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")

        assert "point" in parsed.bundle_types
        assert "x" in parsed.bundle_types["point"].properties
        assert parsed.bundle_types["point"].required == ["x", "y"]


def test_parse_workflow_steps():
    """Test parsing of yaml:steps block in workflows."""
    content = """---
name: test_workflow
type: workflow
---
# Overview
A test workflow.

# Interface
```yaml:schema
inputs:
  n:
    type: integer
outputs:
  result:
    type: integer
```

# Steps
```yaml:steps
- name: step1
  spec: some_function
  inputs:
    x: inputs.n

- name: step2
  spec: another_function
  checkpoint: true
  inputs:
    y: step1.outputs.result
```
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")

        assert parsed.metadata.type == "workflow"
        assert len(parsed.steps) == 2
        assert parsed.steps[0].name == "step1"
        assert parsed.steps[0].spec == "some_function"
        assert parsed.steps[1].checkpoint is True


def test_validate_new_format_function():
    """Test validation of new format function specs."""
    content = """---
name: factorial
type: function
---
# Overview
Computes factorial.

# Interface
```yaml:schema
inputs:
  n: {type: integer}
outputs:
  result: {type: integer}
```

# Behavior
- FR-01: Return 1 when n is 0
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "factorial.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        result = parser.validate_spec("factorial")

        assert result["valid"] is True


def test_validate_bundle_requires_content():
    """Test that bundle validation requires at least one function or type."""
    content = """---
name: empty_bundle
type: bundle
---
# Overview
An empty bundle.
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "empty.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        result = parser.validate_spec("empty")

        assert result["valid"] is False
        assert any("function or type" in e for e in result["errors"])


def test_validate_workflow_requires_steps():
    """Test that workflow validation requires steps."""
    content = """---
name: empty_workflow
type: workflow
---
# Overview
A workflow with no steps.
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "empty.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        result = parser.validate_spec("empty")

        assert result["valid"] is False
        assert any("steps" in e for e in result["errors"])


def test_create_function_template():
    """Test that create_spec generates proper function template."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        parser = SpecParser(tmp_dir)
        path = parser.create_spec("add", "Adds two numbers", "function")

        content = open(path).read()
        assert "name: add" in content
        assert "type: function" in content
        assert "# Overview" in content
        assert "# Interface" in content
        assert "# Behavior" in content


def test_create_bundle_template():
    """Test that create_spec generates proper bundle template."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        parser = SpecParser(tmp_dir)
        path = parser.create_spec("utils", "Utility functions", "bundle")

        content = open(path).read()
        assert "name: utils" in content
        assert "type: bundle" in content
        assert "yaml:functions" in content


def test_create_workflow_template():
    """Test that create_spec generates proper workflow template."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        parser = SpecParser(tmp_dir)
        path = parser.create_spec("pipeline", "A data pipeline", "workflow")

        content = open(path).read()
        assert "name: pipeline" in content
        assert "type: workflow" in content
        assert "yaml:steps" in content


def test_string_dependencies():
    """Test that dependencies can be simple strings."""
    content = """---
name: test_component
type: workflow
dependencies:
  - step1
  - step2
---
# Overview
A workflow.

# Steps
```yaml:steps
- name: s1
  spec: step1
  inputs: {}
```
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)

        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")

        assert parsed.metadata.dependencies == ["step1", "step2"]


def test_parse_arrangement():
    """Test parsing of an Arrangement file."""
    content = """---
target_language: python
output_paths:
  implementation: src/math_utils.py
  tests: tests/test_math_utils.py
environment:
  tools: [uv, pytest]
build_commands:
  test: uv run pytest
constraints:
  - Must use type hints
---
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        parser = SpecParser(tmp_dir)
        arrangement = parser.parse_arrangement(content)

        assert arrangement.target_language == "python"
        assert arrangement.output_paths.implementation == "src/math_utils.py"
        assert arrangement.output_paths.tests == "tests/test_math_utils.py"
        assert arrangement.environment.tools == ["uv", "pytest"]
        assert arrangement.build_commands.test == "uv run pytest"
        assert arrangement.constraints == ["Must use type hints"]
