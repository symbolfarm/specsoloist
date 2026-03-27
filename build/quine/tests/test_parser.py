"""
Tests for SpecParser.
"""

import os
import tempfile
import pytest
from specsoloist.parser import SpecParser, SpecMetadata, ParsedSpec, SPEC_TYPES


class TestSpecTypes:
    """Test the SPEC_TYPES constant."""

    def test_spec_types_contains_all_required_types(self):
        """Test that SPEC_TYPES contains all documented types."""
        assert "function" in SPEC_TYPES
        assert "type" in SPEC_TYPES
        assert "bundle" in SPEC_TYPES
        assert "module" in SPEC_TYPES
        assert "workflow" in SPEC_TYPES
        assert "typedef" in SPEC_TYPES
        assert "class" in SPEC_TYPES
        assert "orchestrator" in SPEC_TYPES
        assert "reference" in SPEC_TYPES


class TestSpecMetadata:
    """Test SpecMetadata dataclass."""

    def test_default_values(self):
        """Test that defaults are set correctly."""
        m = SpecMetadata()
        assert m.name == ""
        assert m.description == ""
        assert m.type == "function"
        assert m.status == "draft"
        assert m.version == ""
        assert m.tags == []
        assert m.dependencies == []
        assert m.language_target is None
        assert m.raw == {}

    def test_custom_values(self):
        """Test setting custom values."""
        m = SpecMetadata(
            name="test",
            description="A test",
            type="bundle",
            status="stable",
            version="1.0.0",
            tags=["foo", "bar"],
            dependencies=["dep1", "dep2"],
            language_target="python"
        )
        assert m.name == "test"
        assert m.description == "A test"
        assert m.type == "bundle"
        assert m.status == "stable"
        assert m.version == "1.0.0"
        assert m.tags == ["foo", "bar"]
        assert m.dependencies == ["dep1", "dep2"]
        assert m.language_target == "python"


class TestSpecParserInit:
    """Test SpecParser initialization."""

    def test_init_with_src_dir(self):
        """Test parser initialization with src directory."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            assert os.path.isabs(parser.src_dir)
            assert parser.src_dir == os.path.abspath(tmp)

    def test_init_with_template_dir(self):
        """Test parser initialization with template override."""
        with tempfile.TemporaryDirectory() as tmp:
            with tempfile.TemporaryDirectory() as template_tmp:
                parser = SpecParser(tmp, template_dir=template_tmp)
                assert parser.template_dir == template_tmp


class TestGetSpecPath:
    """Test get_spec_path method."""

    def test_absolute_path_returned_as_is(self):
        """Test that absolute paths are returned unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            abs_path = "/some/absolute/path.spec.md"
            assert parser.get_spec_path(abs_path) == abs_path

    def test_relative_name_gets_spec_md_suffix(self):
        """Test that relative names get .spec.md suffix."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            result = parser.get_spec_path("myspec")
            assert result.endswith("myspec.spec.md")

    def test_relative_name_with_spec_md_unchanged(self):
        """Test that names with .spec.md suffix are not doubled."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            result = parser.get_spec_path("myspec.spec.md")
            assert result.endswith("myspec.spec.md")
            # Make sure it doesn't end with .spec.md.spec.md
            assert not result.endswith(".spec.md.spec.md")

    def test_relative_path_existing_file_returned_as_is(self):
        """Test that relative paths to existing files are returned as-is."""
        with tempfile.TemporaryDirectory() as tmp:
            # Create a file in current directory (relative to cwd)
            spec_file = "test.spec.md"
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp)
                with open(spec_file, 'w') as f:
                    f.write("content")

                parser = SpecParser("/some/other/dir")
                result = parser.get_spec_path("test.spec.md")
                # Should return the relative path as-is when it exists
                assert result == "test.spec.md"
            finally:
                os.chdir(original_cwd)


class TestListSpecs:
    """Test list_specs method."""

    def test_list_empty_directory(self):
        """Test listing specs in empty directory."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            specs = parser.list_specs()
            assert specs == []

    def test_list_single_spec(self):
        """Test listing with one spec file."""
        with tempfile.TemporaryDirectory() as tmp:
            spec_file = os.path.join(tmp, "test.spec.md")
            with open(spec_file, 'w') as f:
                f.write("---\nname: test\n---")

            parser = SpecParser(tmp)
            specs = parser.list_specs()
            assert "test.spec.md" in specs

    def test_list_multiple_specs(self):
        """Test listing multiple spec files."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["foo", "bar", "baz"]:
                with open(os.path.join(tmp, f"{name}.spec.md"), 'w') as f:
                    f.write("---\nname: test\n---")

            parser = SpecParser(tmp)
            specs = parser.list_specs()
            assert len(specs) >= 3

    def test_list_ignores_non_spec_files(self):
        """Test that non-spec files are ignored."""
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write("---\nname: test\n---")
            with open(os.path.join(tmp, "readme.md"), 'w') as f:
                f.write("# README")

            parser = SpecParser(tmp)
            specs = parser.list_specs()
            assert len(specs) == 1
            assert "test.spec.md" in specs

    def test_list_recursive_subdirectories(self):
        """Test that specs in subdirectories are found."""
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "subdir"))
            with open(os.path.join(tmp, "subdir", "nested.spec.md"), 'w') as f:
                f.write("---\nname: nested\n---")

            parser = SpecParser(tmp)
            specs = parser.list_specs()
            assert any("nested.spec.md" in s for s in specs)

    def test_list_nonexistent_directory(self):
        """Test listing from non-existent directory returns empty list."""
        parser = SpecParser("/nonexistent/path")
        specs = parser.list_specs()
        assert specs == []


class TestReadSpec:
    """Test read_spec method."""

    def test_read_existing_spec(self):
        """Test reading an existing spec file."""
        with tempfile.TemporaryDirectory() as tmp:
            content = "---\nname: test\n---\n# Overview\nTest spec"
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            result = parser.read_spec("test")
            assert result == content

    def test_read_nonexistent_spec_raises_error(self):
        """Test that reading non-existent spec raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            with pytest.raises(FileNotFoundError):
                parser.read_spec("nonexistent")


class TestSpecExists:
    """Test spec_exists method."""

    def test_spec_exists_returns_true(self):
        """Test that existing spec is detected."""
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write("---\nname: test\n---")

            parser = SpecParser(tmp)
            assert parser.spec_exists("test") is True

    def test_spec_exists_returns_false(self):
        """Test that missing spec returns false."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            assert parser.spec_exists("nonexistent") is False


class TestCreateSpec:
    """Test create_spec method."""

    def test_create_function_spec(self):
        """Test creating a function spec."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            path = parser.create_spec("test_func", "Test function", "function")

            assert os.path.exists(path)
            content = open(path).read()
            assert "name: test_func" in content
            assert "type: function" in content
            assert "# Overview" in content
            assert "# Interface" in content
            assert "# Behavior" in content

    def test_create_type_spec(self):
        """Test creating a type spec."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            path = parser.create_spec("test_type", "Test type", "type")

            assert os.path.exists(path)
            content = open(path).read()
            assert "name: test_type" in content
            assert "type: type" in content
            assert "# Overview" in content
            assert "# Schema" in content

    def test_create_bundle_spec(self):
        """Test creating a bundle spec."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            path = parser.create_spec("test_bundle", "Test bundle", "bundle")

            assert os.path.exists(path)
            content = open(path).read()
            assert "name: test_bundle" in content
            assert "type: bundle" in content
            assert "# Overview" in content
            assert "yaml:functions" in content

    def test_create_workflow_spec(self):
        """Test creating a workflow spec."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            path = parser.create_spec("test_workflow", "Test workflow", "workflow")

            assert os.path.exists(path)
            content = open(path).read()
            assert "name: test_workflow" in content
            assert "type: workflow" in content
            assert "# Overview" in content
            assert "yaml:steps" in content
            assert "dependencies:" in content

    def test_create_module_spec(self):
        """Test creating a module spec."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            path = parser.create_spec("test_module", "Test module", "module")

            assert os.path.exists(path)
            content = open(path).read()
            assert "name: test_module" in content
            assert "type: module" in content
            assert "# Overview" in content
            assert "# Exports" in content

    def test_create_spec_already_exists_raises_error(self):
        """Test that creating existing spec raises FileExistsError."""
        with tempfile.TemporaryDirectory() as tmp:
            # Create spec first
            parser = SpecParser(tmp)
            parser.create_spec("test", "Test", "function")

            # Try to create again
            with pytest.raises(FileExistsError):
                parser.create_spec("test", "Test", "function")

    def test_create_spec_creates_parent_directories(self):
        """Test that parent directories are created as needed."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            path = parser.create_spec("subdir/nested/test", "Test", "function")

            assert os.path.exists(path)
            assert os.path.dirname(path).startswith(tmp)


class TestParseFrontmatter:
    """Test frontmatter parsing."""

    def test_parse_metadata_with_description(self):
        """Test that description is parsed from frontmatter."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test_component
description: A explicit description from frontmatter.
---
# Overview
This should be ignored.
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.name == "test_component"
            assert parsed.metadata.description == "A explicit description from frontmatter."

    def test_extract_description_from_overview(self):
        """Test that description is extracted from Overview if missing."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test_component
---
# Overview
This is the extracted description.
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.description == "This is the extracted description."

    def test_extract_description_from_numbered_overview(self):
        """Test extraction from numbered Overview."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test_component
---
# 1. Overview
This is the extracted description.
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.description == "This is the extracted description."

    def test_extract_description_skips_blank_lines(self):
        """Test that blank lines after Overview are skipped."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test_component
---
# Overview


This is the real description.
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.description == "This is the real description."

    def test_parse_tags(self):
        """Test that tags are parsed."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
type: function
tags:
  - math
  - pure
---
# Overview
A function.
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.tags == ["math", "pure"]

    def test_parse_version(self):
        """Test that version is parsed."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
version: 1.2.3
---
# Overview
A versioned component.
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.version == "1.2.3"

    def test_language_target_optional(self):
        """Test that language_target defaults to None."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
type: function
---
# Overview
A language-agnostic spec.
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.language_target is None

    def test_parse_dependencies(self):
        """Test that dependencies are parsed."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
dependencies:
  - dep1
  - dep2
---
# Overview
A component with dependencies.
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.dependencies == ["dep1", "dep2"]

    def test_frontmatter_missing_returns_defaults(self):
        """Test that missing frontmatter uses defaults."""
        with tempfile.TemporaryDirectory() as tmp:
            content = "# Overview\nNo frontmatter"
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert parsed.metadata.name == ""
            assert parsed.metadata.type == "function"
            assert parsed.metadata.status == "draft"


class TestYamlBlockExtraction:
    """Test YAML block extraction."""

    def test_extract_yaml_schema_block(self):
        """Test extracting yaml:schema block."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
---
# Overview
Test

```yaml:schema
inputs:
  x: integer
outputs:
  result: integer
```
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert parsed.schema is not None

    def test_extract_yaml_functions_block(self):
        """Test extracting yaml:functions block."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
type: bundle
---
# Overview
Test

```yaml:functions
add:
  inputs: {a: integer, b: integer}
  outputs: {result: integer}
  behavior: "Add two numbers"
```
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert "add" in parsed.bundle_functions

    def test_extract_yaml_steps_block(self):
        """Test extracting yaml:steps block."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
type: workflow
---
# Overview
Test

```yaml:steps
- name: step1
  spec: spec1
```
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert len(parsed.steps) > 0


class TestValidateSpec:
    """Test validate_spec method."""

    def test_validate_valid_function_spec(self):
        """Test validation of valid function spec."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
type: function
---
# Overview
A function.

# Interface

```yaml:schema
inputs: {}
outputs:
  result: {type: string}
```

# Behavior
- Does something.
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            result = parser.validate_spec("test")

            assert result["valid"] is True
            assert result["errors"] == []

    def test_validate_missing_overview(self):
        """Test that missing Overview is caught."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
type: function
---
# Interface
Something

# Behavior
Something
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            result = parser.validate_spec("test")

            assert result["valid"] is False
            assert any("Overview" in e for e in result["errors"])

    def test_validate_missing_interface(self):
        """Test that missing Interface or schema is caught."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
type: function
---
# Overview
A function

# Behavior
Something
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            result = parser.validate_spec("test")

            assert result["valid"] is False
            assert any("Interface" in e for e in result["errors"])

    def test_validate_bundle_spec(self):
        """Test validation of bundle spec."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
type: bundle
---
# Overview
A bundle

# Functions

```yaml:functions
func1:
  inputs: {}
  outputs: {}
  behavior: "Does something"
```
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            result = parser.validate_spec("test")

            assert result["valid"] is True

    def test_validate_workflow_spec(self):
        """Test validation of workflow spec."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
type: workflow
---
# Overview
A workflow

```yaml:steps
- name: step1
  spec: spec1
```
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            result = parser.validate_spec("test")

            assert result["valid"] is True

    def test_validate_type_spec(self):
        """Test validation of type spec."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
type: type
---
# Overview
A type

# Schema

```yaml:schema
properties:
  field: {type: string}
required: [field]
```
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            result = parser.validate_spec("test")

            assert result["valid"] is True

    def test_validate_nonexistent_spec(self):
        """Test validation of non-existent spec."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            result = parser.validate_spec("nonexistent")

            assert result["valid"] is False
            assert any("not found" in e for e in result["errors"])


class TestGetModuleName:
    """Test get_module_name method."""

    def test_get_module_name(self):
        """Test extracting module name from spec filename."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            name = parser.get_module_name("mymodule.spec.md")
            assert name == "mymodule"

    def test_get_module_name_without_suffix(self):
        """Test with name that doesn't have suffix."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            name = parser.get_module_name("mymodule")
            assert name == "mymodule"


class TestExtractVerificationSnippet:
    """Test extract_verification_snippet method."""

    def test_extract_verification_snippet_present(self):
        """Test extracting code from Verification section."""
        body = """# Overview
Test

# Verification

```python
import test
```

# Next section
"""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            snippet = parser.extract_verification_snippet(body)
            assert "import test" in snippet

    def test_extract_verification_snippet_missing(self):
        """Test with no Verification section."""
        body = """# Overview
Test
"""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            snippet = parser.extract_verification_snippet(body)
            assert snippet == ""

    def test_extract_verification_snippet_no_code(self):
        """Test with Verification section but no code block."""
        body = """# Overview
Test

# Verification

Some text without code.
"""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp)
            snippet = parser.extract_verification_snippet(body)
            assert snippet == ""


class TestLoadGlobalContext:
    """Test load_global_context method."""

    def test_load_global_context_custom_template_dir(self):
        """Test loading from custom template directory."""
        with tempfile.TemporaryDirectory() as tmp:
            with tempfile.TemporaryDirectory() as template_tmp:
                template_file = os.path.join(template_tmp, "global_context.md")
                with open(template_file, 'w') as f:
                    f.write("Global context content")

                parser = SpecParser(tmp, template_dir=template_tmp)
                content = parser.load_global_context()
                assert content == "Global context content"

    def test_load_global_context_missing_returns_empty(self):
        """Test that missing template returns empty string."""
        with tempfile.TemporaryDirectory() as tmp:
            parser = SpecParser(tmp, template_dir=tmp)
            content = parser.load_global_context()
            # Should return empty string if not found
            assert isinstance(content, str)


class TestParseSpec:
    """Test complete parse_spec functionality."""

    def test_parse_function_spec(self):
        """Test parsing function spec."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test_func
type: function
description: A test function
tags: [core]
---
# Overview
Overview text

# Interface

```yaml:schema
inputs:
  x: {type: integer}
outputs:
  result: {type: integer}
```

# Behavior
Does something.
"""
            with open(os.path.join(tmp, "test_func.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test_func")

            assert parsed.metadata.name == "test_func"
            assert parsed.metadata.type == "function"
            assert parsed.metadata.description == "A test function"
            assert "core" in parsed.metadata.tags
            assert parsed.schema is not None
            assert parsed.body.startswith("# Overview")

    def test_parse_spec_body_excludes_frontmatter(self):
        """Test that parsed body excludes frontmatter."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
---
# Overview
Content
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert "name: test" not in parsed.body
            assert "# Overview" in parsed.body

    def test_parse_spec_content_includes_frontmatter(self):
        """Test that content includes full file."""
        with tempfile.TemporaryDirectory() as tmp:
            content = """---
name: test
---
# Overview
Content
"""
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write(content)

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert parsed.content == content

    def test_parse_spec_path_stored(self):
        """Test that spec path is stored."""
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "test.spec.md"), 'w') as f:
                f.write("---\nname: test\n---\n# Overview\nTest")

            parser = SpecParser(tmp)
            parsed = parser.parse_spec("test")

            assert parsed.path.endswith("test.spec.md")
