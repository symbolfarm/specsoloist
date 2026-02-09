"""
Comprehensive tests for SpecParser.

Tests cover:
- Spec file discovery and reading
- Frontmatter parsing and extraction
- YAML block extraction
- Spec creation from templates
- Parsing of different spec types (function, type, bundle, workflow, module)
- Validation of specs
- Edge cases and error conditions
"""

import os
import tempfile
from specsoloist.parser import SpecParser, SpecMetadata, ParsedSpec, SPEC_TYPES


class TestSpecTypes:
    """Tests for SPEC_TYPES constant."""

    def test_spec_types_contains_all_required_types(self):
        """Test that SPEC_TYPES contains all recognized spec types."""
        expected = {"function", "type", "bundle", "module", "workflow", "typedef", "class", "orchestrator"}
        assert SPEC_TYPES == expected


class TestGetSpecPath:
    """Tests for SpecParser.get_spec_path method."""

    def test_get_spec_path_adds_suffix(self):
        """Test that get_spec_path adds .spec.md suffix if missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            path = parser.get_spec_path("myspec")
            assert path.endswith("myspec.spec.md")

    def test_get_spec_path_preserves_suffix(self):
        """Test that get_spec_path doesn't double-add suffix."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            path = parser.get_spec_path("myspec.spec.md")
            assert path.endswith("myspec.spec.md")
            assert not path.endswith("myspec.spec.md.spec.md")

    def test_get_spec_path_returns_absolute(self):
        """Test that get_spec_path returns absolute path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            path = parser.get_spec_path("test")
            assert os.path.isabs(path)

    def test_get_spec_path_with_nested_path(self):
        """Test that get_spec_path handles nested paths."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            path = parser.get_spec_path("subdir/nested/spec")
            assert "subdir/nested/spec.spec.md" in path or "subdir\\nested\\spec.spec.md" in path


class TestListSpecs:
    """Tests for SpecParser.list_specs method."""

    def test_list_specs_empty_directory(self):
        """Test that list_specs returns empty list for empty directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            specs = parser.list_specs()
            assert specs == []

    def test_list_specs_finds_spec_files(self):
        """Test that list_specs finds .spec.md files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create spec files
            spec1 = os.path.join(tmp_dir, "spec1.spec.md")
            spec2 = os.path.join(tmp_dir, "spec2.spec.md")
            open(spec1, 'w').close()
            open(spec2, 'w').close()

            parser = SpecParser(tmp_dir)
            specs = parser.list_specs()

            assert "spec1.spec.md" in specs
            assert "spec2.spec.md" in specs

    def test_list_specs_ignores_non_spec_files(self):
        """Test that list_specs ignores non-.spec.md files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            open(os.path.join(tmp_dir, "readme.md"), 'w').close()
            open(os.path.join(tmp_dir, "test.py"), 'w').close()

            parser = SpecParser(tmp_dir)
            specs = parser.list_specs()

            assert specs == []

    def test_list_specs_nonexistent_directory(self):
        """Test that list_specs returns empty for nonexistent directory."""
        parser = SpecParser("/nonexistent/path")
        specs = parser.list_specs()
        assert specs == []

    def test_list_specs_recursive(self):
        """Test that list_specs finds specs in nested directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            subdir = os.path.join(tmp_dir, "sub")
            os.makedirs(subdir)

            open(os.path.join(tmp_dir, "top.spec.md"), 'w').close()
            open(os.path.join(subdir, "nested.spec.md"), 'w').close()

            parser = SpecParser(tmp_dir)
            specs = parser.list_specs()

            assert any("top.spec.md" in s for s in specs)
            assert any("nested.spec.md" in s for s in specs)


class TestReadSpec:
    """Tests for SpecParser.read_spec method."""

    def test_read_spec_basic(self):
        """Test that read_spec returns file content."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            content = "---\nname: test\n---\n# Overview\nTest spec"
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            read_content = parser.read_spec("test")

            assert read_content == content

    def test_read_spec_not_found(self):
        """Test that read_spec raises FileNotFoundError for missing file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)

            try:
                parser.read_spec("nonexistent")
                assert False, "Should have raised FileNotFoundError"
            except FileNotFoundError as e:
                assert "not found" in str(e)

    def test_read_spec_with_suffix(self):
        """Test that read_spec works with or without .spec.md suffix."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            content = "test content"
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)

            # Both forms should work
            assert parser.read_spec("test") == content
            assert parser.read_spec("test.spec.md") == content


class TestSpecExists:
    """Tests for SpecParser.spec_exists method."""

    def test_spec_exists_true(self):
        """Test that spec_exists returns True for existing file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            open(path, 'w').close()

            parser = SpecParser(tmp_dir)
            assert parser.spec_exists("test") is True

    def test_spec_exists_false(self):
        """Test that spec_exists returns False for missing file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            assert parser.spec_exists("nonexistent") is False


class TestCreateSpec:
    """Tests for SpecParser.create_spec method."""

    def test_create_spec_function(self):
        """Test creating a function spec template."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            path = parser.create_spec("add", "Adds two numbers", "function")

            content = open(path).read()
            assert "name: add" in content
            assert "type: function" in content
            assert "# Overview" in content
            assert "Adds two numbers" in content
            assert "# Interface" in content
            assert "yaml:schema" in content
            assert "# Behavior" in content
            assert "# Examples" in content

    def test_create_spec_type(self):
        """Test creating a type spec template."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            path = parser.create_spec("point", "A 2D point", "type")

            content = open(path).read()
            assert "name: point" in content
            assert "type: type" in content
            assert "# Schema" in content

    def test_create_spec_bundle(self):
        """Test creating a bundle spec template."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            path = parser.create_spec("utils", "Utility functions", "bundle")

            content = open(path).read()
            assert "name: utils" in content
            assert "type: bundle" in content
            assert "yaml:functions" in content

    def test_create_spec_workflow(self):
        """Test creating a workflow spec template."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            path = parser.create_spec("pipeline", "A data pipeline", "workflow")

            content = open(path).read()
            assert "name: pipeline" in content
            assert "type: workflow" in content
            assert "yaml:steps" in content
            assert "dependencies:" in content

    def test_create_spec_module(self):
        """Test creating a module spec template."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            path = parser.create_spec("auth", "Authentication module", "module")

            content = open(path).read()
            assert "name: auth" in content
            assert "type: module" in content
            assert "# Exports" in content

    def test_create_spec_already_exists(self):
        """Test that create_spec raises FileExistsError for existing file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            open(path, 'w').close()

            parser = SpecParser(tmp_dir)

            try:
                parser.create_spec("test", "Description", "function")
                assert False, "Should have raised FileExistsError"
            except FileExistsError as e:
                assert "already exists" in str(e)

    def test_create_spec_creates_directories(self):
        """Test that create_spec creates parent directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            path = parser.create_spec("subdir/nested/spec", "A nested spec", "function")

            assert os.path.exists(path)
            content = open(path).read()
            assert "name: subdir/nested/spec" in content


class TestFrontmatterParsing:
    """Tests for frontmatter parsing in SpecParser._parse_frontmatter."""

    def test_parse_metadata_basic(self):
        """Test basic frontmatter parsing."""
        content = """---
name: test_component
description: A test component.
type: function
---
# Overview
Test content
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.name == "test_component"
            assert parsed.metadata.description == "A test component."
            assert parsed.metadata.type == "function"

    def test_parse_metadata_with_tags(self):
        """Test parsing tags from frontmatter."""
        content = """---
name: test
tags: [math, pure, utility]
---
# Overview
Test
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.tags == ["math", "pure", "utility"]

    def test_parse_metadata_with_status(self):
        """Test parsing status from frontmatter."""
        content = """---
name: test
status: review
---
# Overview
Test
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.status == "review"

    def test_parse_metadata_with_version(self):
        """Test parsing version from frontmatter."""
        content = """---
name: test
version: 1.2.3
---
# Overview
Test
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.version == "1.2.3"

    def test_parse_metadata_language_target_string(self):
        """Test parsing language_target as string."""
        content = """---
name: test
language_target: python
---
# Overview
Test
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.language_target == "python"

    def test_parse_metadata_language_target_list(self):
        """Test parsing language_target as list (uses first element)."""
        content = """---
name: test
language_target: [python, javascript]
---
# Overview
Test
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.language_target == "python"

    def test_parse_metadata_no_language_target(self):
        """Test that language_target defaults to None."""
        content = """---
name: test
---
# Overview
Test
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.language_target is None

    def test_parse_metadata_dependencies_strings(self):
        """Test parsing dependencies as list of strings."""
        content = """---
name: test
dependencies: [dep1, dep2, dep3]
---
# Overview
Test
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.dependencies == ["dep1", "dep2", "dep3"]

    def test_parse_metadata_dependencies_mixed(self):
        """Test parsing dependencies as mixed strings and dicts."""
        content = """---
name: test
dependencies:
  - dep1
  - name: dep2
    version: "1.0"
---
# Overview
Test
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert len(parsed.metadata.dependencies) == 2
            assert parsed.metadata.dependencies[0] == "dep1"
            assert isinstance(parsed.metadata.dependencies[1], dict)

    def test_parse_metadata_no_frontmatter(self):
        """Test parsing file with no frontmatter returns defaults."""
        content = """# Overview
No frontmatter here
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.name == ""
            assert parsed.metadata.type == "function"
            assert parsed.metadata.status == "draft"

    def test_parse_metadata_malformed_yaml(self):
        """Test parsing malformed frontmatter returns defaults."""
        content = """---
name: test
  invalid:
    indentation: here
type
---
# Overview
Content
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            # Should return defaults due to YAML error
            assert parsed.metadata.name == ""


class TestDescriptionExtraction:
    """Tests for description extraction from Overview section."""

    def test_extract_description_from_overview(self):
        """Test extracting description from # Overview."""
        content = """---
name: test
---
# Overview
This is the description.

# Next Section
More content
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.description == "This is the description."

    def test_extract_description_from_numbered_overview(self):
        """Test extracting description from # 1. Overview."""
        content = """---
name: test
---
# 1. Overview
Description from numbered section.

# 2. Next
Content
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.description == "Description from numbered section."

    def test_extract_description_skips_blank_lines(self):
        """Test that description extraction skips blank lines."""
        content = """---
name: test
---
# Overview


Actual description after blank lines.
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.description == "Actual description after blank lines."

    def test_description_frontmatter_takes_precedence(self):
        """Test that frontmatter description takes precedence over Overview."""
        content = """---
name: test
description: Frontmatter description
---
# Overview
Overview description
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.description == "Frontmatter description"


class TestYAMLBlockExtraction:
    """Tests for YAML block extraction."""

    def test_extract_yaml_schema_block(self):
        """Test extracting yaml:schema block."""
        content = """---
name: test
---
# Overview
Test

# Interface
```yaml:schema
inputs:
  x: integer
outputs:
  result: integer
```

# Behavior
Describe behavior
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.schema is not None
            assert len(parsed.schema.inputs) > 0
            assert len(parsed.schema.outputs) > 0

    def test_extract_yaml_functions_block(self):
        """Test extracting yaml:functions block."""
        content = """---
name: test
type: bundle
---
# Overview
Test

# Functions
```yaml:functions
func1:
  inputs: {a: integer}
  outputs: {result: integer}
  behavior: Do something
```
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert "func1" in parsed.bundle_functions

    def test_extract_yaml_types_block(self):
        """Test extracting yaml:types block."""
        content = """---
name: test
type: bundle
---
# Overview
Test

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

    def test_extract_yaml_steps_block(self):
        """Test extracting yaml:steps block."""
        content = """---
name: test
type: workflow
---
# Overview
Test

# Steps
```yaml:steps
- name: step1
  spec: func1
  inputs:
    x: inputs.value

- name: step2
  spec: func2
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

            assert len(parsed.steps) == 2
            assert parsed.steps[0].name == "step1"
            assert parsed.steps[1].name == "step2"

    def test_yaml_block_not_found(self):
        """Test that missing YAML block returns None."""
        content = """---
name: test
---
# Overview
No yaml blocks here
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.schema is None
            assert parsed.bundle_functions == {}
            assert parsed.bundle_types == {}
            assert parsed.steps == []


class TestSpecParsing:
    """Tests for complete spec parsing."""

    def test_parse_function_spec(self):
        """Test parsing a complete function spec."""
        content = """---
name: add
description: Adds two numbers
type: function
version: 1.0.0
tags: [math, pure]
---
# Overview
Adds two positive integers.

# Interface
```yaml:schema
inputs:
  a: {type: integer, minimum: 0}
  b: {type: integer, minimum: 0}
outputs:
  sum: {type: integer}
```

# Behavior
- FR-01: Return the sum of a and b

# Examples
| a | b | sum |
|---|---|-----|
| 1 | 2 | 3   |
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "add.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("add")

            assert parsed.metadata.name == "add"
            assert parsed.metadata.type == "function"
            assert parsed.metadata.version == "1.0.0"
            assert parsed.schema is not None

    def test_parse_type_spec(self):
        """Test parsing a type spec."""
        content = """---
name: point
type: type
---
# Overview
A 2D point in space.

# Schema
```yaml:schema
properties:
  x: {type: number}
  y: {type: number}
required: [x, y]
```
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "point.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("point")

            assert parsed.metadata.type == "type"
            assert parsed.schema is not None

    def test_parse_bundle_spec(self):
        """Test parsing a bundle spec."""
        content = """---
name: math
type: bundle
---
# Overview
Math utilities.

# Functions
```yaml:functions
add:
  inputs: {a: integer, b: integer}
  outputs: {result: integer}
  behavior: Return sum

subtract:
  inputs: {a: integer, b: integer}
  outputs: {result: integer}
  behavior: Return difference
```
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "math.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("math")

            assert parsed.metadata.type == "bundle"
            assert len(parsed.bundle_functions) == 2

    def test_parse_workflow_spec(self):
        """Test parsing a workflow spec."""
        content = """---
name: process
type: workflow
dependencies: [step1, step2]
---
# Overview
Process data pipeline.

# Interface
```yaml:schema
inputs:
  raw_data: {type: string}
outputs:
  result: {type: string}
```

# Steps
```yaml:steps
- name: validate
  spec: step1
  inputs:
    data: inputs.raw_data

- name: transform
  spec: step2
  inputs:
    data: validate.outputs.result
```
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "process.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("process")

            assert parsed.metadata.type == "workflow"
            assert len(parsed.steps) == 2
            assert parsed.metadata.dependencies == ["step1", "step2"]

    def test_parse_module_spec(self):
        """Test parsing a module spec."""
        content = """---
name: auth
type: module
---
# Overview
Authentication module.

# Exports
- `login`: Authenticate a user
- `logout`: End user session
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "auth.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("auth")

            assert parsed.metadata.type == "module"


class TestSpecValidation:
    """Tests for spec validation."""

    def test_validate_function_spec_valid(self):
        """Test validation of a valid function spec."""
        content = """---
name: test
type: function
---
# Overview
A test function.

# Interface
```yaml:schema
inputs:
  x: integer
outputs:
  result: integer
```

# Behavior
- FR-01: Return x times 2
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is True
            assert result["errors"] == []

    def test_validate_function_spec_missing_overview(self):
        """Test that function validation fails without Overview."""
        content = """---
name: test
type: function
---
# Interface
Some interface

# Behavior
Some behavior
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is False
            assert any("Overview" in e for e in result["errors"])

    def test_validate_function_spec_missing_interface(self):
        """Test that function validation fails without Interface."""
        content = """---
name: test
type: function
---
# Overview
A function

# Behavior
Does something
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is False
            assert any("Interface" in e or "yaml:schema" in e for e in result["errors"])

    def test_validate_function_spec_missing_behavior(self):
        """Test that function validation fails without Behavior."""
        content = """---
name: test
type: function
---
# Overview
A function

# Interface
```yaml:schema
inputs:
  x: integer
outputs:
  result: integer
```
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is False
            assert any("Behavior" in e for e in result["errors"])

    def test_validate_type_spec_valid(self):
        """Test validation of a valid type spec."""
        content = """---
name: test
type: type
---
# Overview
A type definition.

# Schema
```yaml:schema
properties:
  x: {type: number}
required: [x]
```
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is True

    def test_validate_bundle_spec_valid(self):
        """Test validation of a valid bundle spec."""
        content = """---
name: test
type: bundle
---
# Overview
A bundle of functions.

# Functions
```yaml:functions
func:
  inputs: {x: integer}
  outputs: {result: integer}
  behavior: Do something
```
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is True

    def test_validate_bundle_spec_empty(self):
        """Test that empty bundle validation fails."""
        content = """---
name: test
type: bundle
---
# Overview
Empty bundle.
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is False
            assert any("function or type" in e for e in result["errors"])

    def test_validate_workflow_spec_valid(self):
        """Test validation of a valid workflow spec."""
        content = """---
name: test
type: workflow
---
# Overview
A workflow.

# Steps
```yaml:steps
- name: step1
  spec: func1
  inputs: {}
```
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is True

    def test_validate_workflow_spec_no_steps(self):
        """Test that workflow without steps fails validation."""
        content = """---
name: test
type: workflow
---
# Overview
A workflow without steps.
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is False
            assert any("steps" in e for e in result["errors"])

    def test_validate_module_spec_valid(self):
        """Test validation of a valid module spec."""
        content = """---
name: test
type: module
---
# Overview
A module.

# Exports
- `func1`: Do something
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is True

    def test_validate_missing_file(self):
        """Test that validation of missing file returns appropriate error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("nonexistent")

            assert result["valid"] is False
            assert any("not found" in e for e in result["errors"])

    def test_validate_no_frontmatter(self):
        """Test that validation fails without frontmatter."""
        content = """# Overview
No frontmatter.
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is False
            assert any("frontmatter" in e for e in result["errors"])


class TestGetModuleName:
    """Tests for SpecParser.get_module_name method."""

    def test_get_module_name_with_suffix(self):
        """Test that get_module_name strips .spec.md suffix."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            name = parser.get_module_name("mymodule.spec.md")
            assert name == "mymodule"

    def test_get_module_name_without_suffix(self):
        """Test that get_module_name handles names without suffix."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            name = parser.get_module_name("mymodule")
            assert name == "mymodule"

    def test_get_module_name_nested(self):
        """Test that get_module_name handles nested paths."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir)
            name = parser.get_module_name("subdir/nested/module.spec.md")
            assert name == "subdir/nested/module"


class TestLoadGlobalContext:
    """Tests for SpecParser.load_global_context method."""

    def test_load_global_context_custom_dir(self):
        """Test loading global_context from custom template directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_dir = os.path.join(tmp_dir, "templates")
            os.makedirs(template_dir)

            context_file = os.path.join(template_dir, "global_context.md")
            with open(context_file, 'w') as f:
                f.write("# Global Context\nTest content")

            parser = SpecParser(tmp_dir, template_dir=template_dir)
            context = parser.load_global_context()

            assert "Global Context" in context
            assert "Test content" in context

    def test_load_global_context_missing(self):
        """Test that load_global_context returns empty string if not found."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            parser = SpecParser(tmp_dir, template_dir=tmp_dir)
            context = parser.load_global_context()

            assert context == ""


class TestParsedSpecDataclass:
    """Tests for ParsedSpec dataclass."""

    def test_parsed_spec_creation(self):
        """Test creating a ParsedSpec instance."""
        metadata = SpecMetadata(name="test", type="function")
        parsed = ParsedSpec(
            metadata=metadata,
            content="test content",
            body="body",
            path="/path/to/test.spec.md"
        )

        assert parsed.metadata.name == "test"
        assert parsed.content == "test content"
        assert parsed.body == "body"
        assert parsed.schema is None
        assert parsed.bundle_functions == {}


class TestSpecMetadataDataclass:
    """Tests for SpecMetadata dataclass."""

    def test_metadata_defaults(self):
        """Test SpecMetadata defaults."""
        metadata = SpecMetadata()

        assert metadata.name == ""
        assert metadata.description == ""
        assert metadata.type == "function"
        assert metadata.status == "draft"
        assert metadata.version == ""
        assert metadata.tags == []
        assert metadata.dependencies == []
        assert metadata.language_target is None
        assert metadata.raw == {}

    def test_metadata_with_values(self):
        """Test SpecMetadata with custom values."""
        metadata = SpecMetadata(
            name="test",
            description="A test",
            type="bundle",
            status="stable",
            version="1.0.0",
            tags=["math"],
            dependencies=["dep1"],
            language_target="python"
        )

        assert metadata.name == "test"
        assert metadata.description == "A test"
        assert metadata.type == "bundle"
        assert metadata.status == "stable"
        assert metadata.version == "1.0.0"
        assert metadata.tags == ["math"]
        assert metadata.dependencies == ["dep1"]
        assert metadata.language_target == "python"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_workflow_attaches_steps_to_schema(self):
        """Test that workflow parser attaches steps to schema."""
        content = """---
name: test
type: workflow
---
# Overview
Test

# Interface
```yaml:schema
inputs:
  x: integer
outputs:
  result: integer
```

# Steps
```yaml:steps
- name: s1
  spec: f1
  inputs: {}
```
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert parsed.schema is not None
            assert parsed.schema.steps is not None
            assert len(parsed.schema.steps) == 1

    def test_orchestrator_type_treated_like_workflow(self):
        """Test that orchestrator type is treated like workflow."""
        content = """---
name: test
type: orchestrator
---
# Overview
Test

# Steps
```yaml:steps
- name: s1
  spec: f1
  inputs: {}
```
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            parsed = parser.parse_spec("test")

            assert len(parsed.steps) > 0

    def test_class_type_validated_like_function(self):
        """Test that class type is validated like function."""
        content = """---
name: test
type: class
---
# Overview
Test

# Interface
```yaml:schema
inputs: {}
outputs: {}
```

# Behavior
Test behavior
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is True

    def test_numbered_sections_recognized(self):
        """Test that numbered sections are recognized in validation."""
        content = """---
name: test
type: function
---
# 1. Overview
Test function

# 2. Interface Specification
```yaml:schema
inputs: {}
outputs: {}
```

# 3. Functional Requirements
Test behavior
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            assert result["valid"] is True

    def test_specification_type_no_validation(self):
        """Test that specification type has no additional validation."""
        content = """---
name: test
type: specification
---
Any content
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "test.spec.md")
            with open(path, 'w') as f:
                f.write(content)

            parser = SpecParser(tmp_dir)
            result = parser.validate_spec("test")

            # Only checks for frontmatter
            assert result["valid"] is True
