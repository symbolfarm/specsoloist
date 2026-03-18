"""Tests for the parser module."""

import os
import pytest
import tempfile

from specsoloist.parser import (
    SPEC_TYPES,
    ParsedSpec,
    SpecMetadata,
    SpecParser,
)


SIMPLE_FUNCTION_SPEC = """---
name: my_func
description: Does something useful
type: function
status: stable
version: 1.0.0
tags:
  - math
  - pure
dependencies: []
---

# Overview

Does something useful

# Interface

```yaml:schema
inputs:
  x: {type: integer}
outputs:
  result: {type: integer}
```

# Behavior

- FR1: Doubles the input

# Examples

| Input | Output |
|-------|--------|
| 5 | 10 |
"""

BUNDLE_SPEC = """---
name: mymodule
type: bundle
---

# Overview

A bundle module.

# Functions

```yaml:functions
add:
  inputs:
    a: {type: integer}
    b: {type: integer}
  outputs:
    result: {type: integer}
  behavior: "Add two numbers"
```

# Types

```yaml:types
Point:
  properties:
    x: {type: number}
    y: {type: number}
  required: [x, y]
```
"""

WORKFLOW_SPEC = """---
name: my_workflow
type: workflow
dependencies: [step1, step2]
---

# Overview

A workflow.

# Interface

```yaml:schema
inputs:
  data: {type: string}
outputs:
  result: {type: string}
```

# Steps

```yaml:steps
- name: process
  spec: step1
  inputs:
    data: data
- name: finalize
  spec: step2
  checkpoint: true
  inputs:
    processed: process.outputs.result
```

# Error Handling

TODO
"""


@pytest.fixture
def spec_dir(tmp_path):
    """Create a temp directory with sample specs."""
    # Write specs
    (tmp_path / "my_func.spec.md").write_text(SIMPLE_FUNCTION_SPEC)
    (tmp_path / "mymodule.spec.md").write_text(BUNDLE_SPEC)
    (tmp_path / "my_workflow.spec.md").write_text(WORKFLOW_SPEC)
    return tmp_path


@pytest.fixture
def parser(spec_dir):
    return SpecParser(str(spec_dir))


class TestSpecTypes:
    def test_spec_types_is_set(self):
        assert isinstance(SPEC_TYPES, (set, frozenset))

    def test_expected_types_present(self):
        expected = {"function", "type", "bundle", "module", "workflow", "reference"}
        for t in expected:
            assert t in SPEC_TYPES


class TestSpecParser:
    def test_init(self, tmp_path):
        p = SpecParser(str(tmp_path))
        assert os.path.isabs(p.src_dir)

    def test_get_spec_path_adds_suffix(self, parser, spec_dir):
        path = parser.get_spec_path("my_func")
        assert path.endswith("my_func.spec.md")

    def test_get_spec_path_absolute(self, parser, tmp_path):
        abs_path = str(tmp_path / "other.spec.md")
        assert parser.get_spec_path(abs_path) == abs_path

    def test_list_specs(self, parser):
        specs = parser.list_specs()
        assert len(specs) >= 3
        names = [os.path.basename(s).replace(".spec.md", "") for s in specs]
        assert "my_func" in names
        assert "mymodule" in names

    def test_list_specs_empty_dir(self, tmp_path):
        p = SpecParser(str(tmp_path / "nonexistent"))
        assert p.list_specs() == []

    def test_read_spec(self, parser):
        content = parser.read_spec("my_func")
        assert "my_func" in content
        assert "# Overview" in content

    def test_read_spec_missing_raises(self, parser):
        with pytest.raises(FileNotFoundError):
            parser.read_spec("nonexistent_spec")

    def test_spec_exists_true(self, parser):
        assert parser.spec_exists("my_func") is True

    def test_spec_exists_false(self, parser):
        assert parser.spec_exists("nonexistent") is False

    def test_create_spec_function(self, tmp_path):
        p = SpecParser(str(tmp_path))
        path = p.create_spec("new_func", "A new function", "function")
        assert os.path.exists(path)
        content = open(path).read()
        assert "name: new_func" in content
        assert "type: function" in content
        assert "# Overview" in content

    def test_create_spec_bundle(self, tmp_path):
        p = SpecParser(str(tmp_path))
        path = p.create_spec("new_bundle", "A new bundle", "bundle")
        assert os.path.exists(path)
        content = open(path).read()
        assert "type: bundle" in content

    def test_create_spec_workflow(self, tmp_path):
        p = SpecParser(str(tmp_path))
        path = p.create_spec("new_wf", "A workflow", "workflow")
        assert os.path.exists(path)
        content = open(path).read()
        assert "type: workflow" in content

    def test_create_spec_exists_raises(self, parser):
        with pytest.raises(FileExistsError):
            parser.create_spec("my_func", "Already exists", "function")

    def test_parse_function_spec(self, parser):
        spec = parser.parse_spec("my_func")
        assert isinstance(spec, ParsedSpec)
        assert spec.metadata.name == "my_func"
        assert spec.metadata.type == "function"
        assert spec.metadata.status == "stable"
        assert spec.metadata.version == "1.0.0"
        assert "math" in spec.metadata.tags

    def test_parse_function_spec_schema(self, parser):
        spec = parser.parse_spec("my_func")
        assert spec.schema is not None
        assert "x" in spec.schema.inputs
        assert spec.schema.inputs["x"].type == "integer"

    def test_parse_bundle_spec(self, parser):
        spec = parser.parse_spec("mymodule")
        assert spec.metadata.type == "bundle"
        assert "add" in spec.bundle_functions
        assert "Point" in spec.bundle_types

    def test_parse_bundle_functions(self, parser):
        spec = parser.parse_spec("mymodule")
        add_func = spec.bundle_functions["add"]
        assert add_func.behavior == "Add two numbers"

    def test_parse_workflow_spec(self, parser):
        spec = parser.parse_spec("my_workflow")
        assert spec.metadata.type == "workflow"
        assert len(spec.steps) == 2
        assert spec.steps[0].name == "process"
        assert spec.steps[1].checkpoint is True

    def test_parse_description_fallback(self, tmp_path):
        spec_content = """---
name: no_desc
type: function
---

# Overview

Extracted description from body.

# Behavior

FR1: Do something.
"""
        (tmp_path / "no_desc.spec.md").write_text(spec_content)
        p = SpecParser(str(tmp_path))
        spec = p.parse_spec("no_desc")
        assert spec.metadata.description == "Extracted description from body."

    def test_parse_body_strips_frontmatter(self, parser):
        spec = parser.parse_spec("my_func")
        assert not spec.body.startswith("---")
        assert "# Overview" in spec.body

    def test_parse_content_includes_frontmatter(self, parser):
        spec = parser.parse_spec("my_func")
        assert spec.content.startswith("---")

    def test_parse_path_is_absolute(self, parser):
        spec = parser.parse_spec("my_func")
        assert os.path.isabs(spec.path)

    def test_validate_valid_function(self, parser):
        result = parser.validate_spec("my_func")
        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_bundle(self, parser):
        result = parser.validate_spec("mymodule")
        assert result["valid"] is True

    def test_validate_missing_spec(self, parser):
        result = parser.validate_spec("nonexistent")
        assert result["valid"] is False
        assert any("not found" in e.lower() for e in result["errors"])

    def test_validate_invalid_bundle(self, tmp_path):
        spec_content = """---
name: empty_bundle
type: bundle
---

# Overview

No functions or types here.
"""
        (tmp_path / "empty_bundle.spec.md").write_text(spec_content)
        p = SpecParser(str(tmp_path))
        result = p.validate_spec("empty_bundle")
        assert result["valid"] is False

    def test_get_module_name(self, parser):
        assert parser.get_module_name("my_func.spec.md") == "my_func"
        assert parser.get_module_name("path/to/foo.spec.md") == "foo.spec.md".replace(".spec.md", "")

    def test_extract_verification_snippet(self, parser):
        body = """# Overview

Some description.

# Verification

```python
assert foo() == 1
```

# Other
"""
        result = parser.extract_verification_snippet(body)
        assert "assert foo() == 1" in result

    def test_extract_verification_snippet_missing(self, parser):
        body = "# Overview\n\nNo verification section."
        result = parser.extract_verification_snippet(body)
        assert result == ""

    def test_parse_alias(self, parser):
        """parse() should be an alias for parse_spec()."""
        spec1 = parser.parse_spec("my_func")
        spec2 = parser.parse("my_func")
        assert spec1.metadata.name == spec2.metadata.name


class TestFrontmatterParsing:
    def test_tags_parsed_as_list(self, tmp_path):
        spec_content = """---
name: tagged
type: function
tags: [math, pure]
---

# Overview

Tagged spec.

# Interface

```yaml:schema
inputs: {}
outputs: {}
```

# Behavior

FR1: Does something.
"""
        (tmp_path / "tagged.spec.md").write_text(spec_content)
        p = SpecParser(str(tmp_path))
        spec = p.parse_spec("tagged")
        assert spec.metadata.tags == ["math", "pure"]

    def test_dependencies_as_list(self, tmp_path):
        spec_content = """---
name: dep_spec
type: bundle
dependencies:
  - dep1
  - dep2
---

# Overview

Has deps.

# Functions

```yaml:functions
foo:
  inputs: {}
  outputs: {}
  behavior: "foo"
```
"""
        (tmp_path / "dep_spec.spec.md").write_text(spec_content)
        p = SpecParser(str(tmp_path))
        spec = p.parse_spec("dep_spec")
        assert spec.metadata.dependencies == ["dep1", "dep2"]

    def test_no_frontmatter(self, tmp_path):
        spec_content = "# Just a plain markdown file\n\nNo frontmatter here."
        (tmp_path / "plain.spec.md").write_text(spec_content)
        p = SpecParser(str(tmp_path))
        spec = p.parse_spec("plain")
        assert spec.metadata.name == ""
