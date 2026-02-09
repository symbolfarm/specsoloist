"""
Tests for SpecComposer module.

Tests the composer's ability to:
- Draft architectures from natural language requests
- Parse LLM responses into Architecture objects
- Generate spec files
- Handle errors gracefully
"""

import os
import tempfile
from unittest.mock import Mock, patch
import yaml
import pytest

from spechestra.speccomposer import (
    ComponentDef,
    Architecture,
    CompositionResult,
    SpecComposer,
)
from specsoloist.config import SpecSoloistConfig
from specsoloist.parser import SpecParser


class TestComponentDef:
    """Tests for ComponentDef dataclass."""

    def test_component_def_creation(self):
        """Test creating a component definition."""
        comp = ComponentDef(
            name="auth",
            type="module",
            description="Authentication module"
        )
        assert comp.name == "auth"
        assert comp.type == "module"
        assert comp.description == "Authentication module"
        assert comp.inputs == {}
        assert comp.outputs == {}
        assert comp.dependencies == []

    def test_component_def_with_dependencies(self):
        """Test component with dependencies."""
        comp = ComponentDef(
            name="service",
            type="bundle",
            description="Main service",
            dependencies=["auth", "db"]
        )
        assert comp.dependencies == ["auth", "db"]

    def test_component_def_with_inputs_outputs(self):
        """Test component with inputs and outputs."""
        comp = ComponentDef(
            name="processor",
            type="function",
            description="Data processor",
            inputs={"data": "string"},
            outputs={"result": "string"}
        )
        assert comp.inputs == {"data": "string"}
        assert comp.outputs == {"result": "string"}


class TestArchitecture:
    """Tests for Architecture dataclass."""

    def test_architecture_creation(self):
        """Test creating an architecture."""
        arch = Architecture(
            components=[
                ComponentDef(name="auth", type="module", description="Auth"),
                ComponentDef(name="db", type="module", description="Database")
            ],
            dependencies={"db": []},
            build_order=["db", "auth"]
        )
        assert len(arch.components) == 2
        assert arch.build_order == ["db", "auth"]

    def test_architecture_to_yaml(self):
        """Test serializing architecture to YAML."""
        comp1 = ComponentDef(name="comp1", type="function", description="Comp 1")
        comp2 = ComponentDef(name="comp2", type="module", description="Comp 2", dependencies=["comp1"])
        arch = Architecture(
            components=[comp1, comp2],
            dependencies={"comp1": [], "comp2": ["comp1"]},
            build_order=["comp1", "comp2"],
            description="Test architecture"
        )

        yaml_str = arch.to_yaml()
        assert "comp1" in yaml_str
        assert "comp2" in yaml_str
        assert "Test architecture" in yaml_str

    def test_architecture_from_yaml(self):
        """Test parsing architecture from YAML."""
        yaml_str = """
components:
  - name: auth
    type: module
    description: Authentication module
    dependencies: []
  - name: db
    type: module
    description: Database module
    dependencies: []
build_order:
  - db
  - auth
description: Test system
"""
        arch = Architecture.from_yaml(yaml_str)
        assert len(arch.components) == 2
        assert arch.components[0].name == "auth"
        assert arch.components[1].name == "db"
        assert arch.build_order == ["db", "auth"]
        assert arch.description == "Test system"

    def test_architecture_from_yaml_with_dependencies(self):
        """Test parsing architecture with component dependencies from YAML."""
        yaml_str = """
components:
  - name: auth
    type: module
    description: Authentication
    dependencies: []
  - name: api
    type: module
    description: API service
    dependencies:
      - auth
build_order:
  - auth
  - api
"""
        arch = Architecture.from_yaml(yaml_str)
        assert arch.components[0].dependencies == []
        assert arch.components[1].dependencies == ["auth"]
        assert arch.dependencies["api"] == ["auth"]


class TestCompositionResult:
    """Tests for CompositionResult dataclass."""

    def test_composition_result_success(self):
        """Test successful composition result."""
        arch = Architecture(components=[], dependencies={}, build_order=[])
        result = CompositionResult(
            architecture=arch,
            spec_paths=["/path/to/spec.md"],
            ready_for_build=True
        )
        assert result.ready_for_build is True
        assert result.cancelled is False
        assert len(result.spec_paths) == 1

    def test_composition_result_cancelled(self):
        """Test cancelled composition result."""
        arch = Architecture(components=[], dependencies={}, build_order=[])
        result = CompositionResult(
            architecture=arch,
            spec_paths=[],
            ready_for_build=False,
            cancelled=True
        )
        assert result.cancelled is True
        assert result.ready_for_build is False


class TestSpecComposer:
    """Tests for SpecComposer class."""

    def test_composer_initialization(self):
        """Test initializing the composer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = SpecComposer(tmpdir)
            assert composer.project_dir == os.path.abspath(tmpdir)
            assert composer.config is not None
            assert composer.parser is not None

    def test_composer_with_config(self):
        """Test initializing composer with explicit config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            composer = SpecComposer(tmpdir, config=config)
            assert composer.config is config

    def test_composer_with_provider(self):
        """Test initializing composer with explicit provider."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_provider = Mock()
            composer = SpecComposer(tmpdir, provider=mock_provider)
            assert composer._provider is mock_provider

    def test_composer_lazy_provider(self):
        """Test that provider is created lazily."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use explicit provider to avoid needing API key
            mock_provider = Mock()
            composer = SpecComposer(tmpdir, provider=mock_provider)
            assert composer._provider is mock_provider
            # Getting provider should return same instance
            provider = composer._get_provider()
            assert provider is mock_provider
            # Second call should return same instance
            provider2 = composer._get_provider()
            assert provider is provider2

    def test_parse_architecture_response_valid_yaml(self):
        """Test parsing valid YAML response."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = SpecComposer(tmpdir)
            response = """
```yaml
description: Test system
components:
  - name: auth
    type: module
    description: Auth module
    dependencies: []
  - name: api
    type: bundle
    description: API service
    dependencies:
      - auth
build_order:
  - auth
  - api
```
"""
            arch = composer._parse_architecture_response(response)
            assert len(arch.components) == 2
            assert arch.components[0].name == "auth"
            assert arch.components[1].name == "api"
            assert arch.components[1].dependencies == ["auth"]
            assert arch.build_order == ["auth", "api"]

    def test_parse_architecture_response_invalid_yaml(self):
        """Test parsing invalid YAML response."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = SpecComposer(tmpdir)
            response = """
```yaml
this is not valid yaml: [
```
"""
            arch = composer._parse_architecture_response(response)
            assert len(arch.components) == 0
            assert arch.build_order == []

    def test_parse_architecture_response_without_yaml_fence(self):
        """Test parsing response without YAML fences."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = SpecComposer(tmpdir)
            response = """description: Test
components: []
build_order: []
"""
            arch = composer._parse_architecture_response(response)
            assert arch.description == "Test"
            assert len(arch.components) == 0

    def test_parse_architecture_response_non_dict(self):
        """Test parsing response that doesn't parse to dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            composer = SpecComposer(tmpdir)
            response = "```yaml\n- item1\n- item2\n```"
            arch = composer._parse_architecture_response(response)
            assert len(arch.components) == 0

    def test_draft_architecture(self):
        """Test drafting architecture with LLM."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_provider = Mock()
            mock_provider.generate.return_value = """```yaml
description: Todo app system
components:
  - name: models
    type: bundle
    description: Data models
    dependencies: []
  - name: api
    type: module
    description: REST API
    dependencies:
      - models
build_order:
  - models
  - api
```"""
            composer = SpecComposer(tmpdir, provider=mock_provider)

            arch = composer.draft_architecture("Build a todo app")
            assert len(arch.components) == 2
            assert arch.components[0].name == "models"
            assert arch.components[1].name == "api"
            mock_provider.generate.assert_called_once()

    def test_draft_architecture_with_context(self):
        """Test drafting architecture with existing specs as context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_provider = Mock()
            mock_provider.generate.return_value = """```yaml
components: []
build_order: []
"""
            composer = SpecComposer(tmpdir, provider=mock_provider)

            context = {"existing_specs": ["auth.spec.md", "db.spec.md"]}
            composer.draft_architecture("Extend the system", context=context)

            call_args = mock_provider.generate.call_args[0][0]
            assert "auth.spec.md" in call_args
            assert "db.spec.md" in call_args

    def test_generate_specs_creates_files(self):
        """Test that generate_specs creates spec files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            mock_provider = Mock()
            mock_provider.generate.return_value = """---
name: test_component
type: function
---

# Overview
Test component
"""
            composer = SpecComposer(tmpdir, config=config, provider=mock_provider)

            comp = ComponentDef(name="test_component", type="function", description="Test")
            arch = Architecture(components=[comp], dependencies={}, build_order=[])

            paths = composer.generate_specs(arch)
            assert len(paths) == 1
            assert "test_component.spec.md" in paths[0]
            assert os.path.exists(paths[0])

    def test_generate_specs_skips_existing(self):
        """Test that generate_specs skips existing specs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            composer = SpecComposer(tmpdir, config=config)

            # Create a spec file manually
            spec_path = os.path.join(config.src_path, "existing.spec.md")
            os.makedirs(os.path.dirname(spec_path), exist_ok=True)
            with open(spec_path, 'w') as f:
                f.write("---\nname: existing\ntype: function\n---\n")

            comp = ComponentDef(name="existing", type="function", description="Existing")
            arch = Architecture(components=[comp], dependencies={}, build_order=[])

            paths = composer.generate_specs(arch)
            # Should be empty because spec already exists
            assert len(paths) == 0

    def test_generate_specs_multiple_components(self):
        """Test generating specs for multiple components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            mock_provider = Mock()
            mock_provider.generate.return_value = """---
name: component
type: function
---

# Overview
Component
"""
            composer = SpecComposer(tmpdir, config=config, provider=mock_provider)

            comps = [
                ComponentDef(name="comp1", type="function", description="Comp 1"),
                ComponentDef(name="comp2", type="module", description="Comp 2"),
                ComponentDef(name="comp3", type="bundle", description="Comp 3")
            ]
            arch = Architecture(components=comps, dependencies={}, build_order=[])

            paths = composer.generate_specs(arch)
            assert len(paths) == 3
            assert all(os.path.exists(p) for p in paths)

    def test_generate_specs_creates_directories(self):
        """Test that generate_specs creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            mock_provider = Mock()
            mock_provider.generate.return_value = """---
name: test
type: function
---

# Overview
Test
"""
            composer = SpecComposer(tmpdir, config=config, provider=mock_provider)

            comp = ComponentDef(name="test", type="function", description="Test")
            arch = Architecture(components=[comp], dependencies={}, build_order=[])

            # Ensure src directory doesn't exist
            assert not os.path.exists(config.src_path)

            paths = composer.generate_specs(arch)
            assert os.path.exists(config.src_path)
            assert all(os.path.exists(p) for p in paths)

    def test_compose_full_workflow(self):
        """Test the full compose workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            mock_provider = Mock()

            # First call returns architecture
            arch_response = """```yaml
description: Simple app
components:
  - name: models
    type: bundle
    description: Data models
    dependencies: []
build_order:
  - models
```"""

            # Second call returns spec content
            spec_response = """---
name: models
type: bundle
---

# Overview
Data models for the app
"""
            mock_provider.generate.side_effect = [arch_response, spec_response]

            composer = SpecComposer(tmpdir, config=config, provider=mock_provider)
            result = composer.compose("Build a simple app")

            assert result.ready_for_build is True
            assert result.cancelled is False
            assert len(result.spec_paths) == 1
            assert "models.spec.md" in result.spec_paths[0]

    def test_compose_empty_architecture(self):
        """Test compose when architecture has no components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_provider = Mock()
            mock_provider.generate.return_value = """```yaml
components: []
build_order: []
```"""
            composer = SpecComposer(tmpdir, provider=mock_provider)

            result = composer.compose("Invalid request")
            assert result.ready_for_build is False
            assert result.cancelled is True
            assert len(result.spec_paths) == 0

    def test_compose_discovers_existing_specs(self):
        """Test that compose discovers existing specs automatically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)

            # Create an existing spec
            spec_path = os.path.join(config.src_path, "existing.spec.md")
            os.makedirs(os.path.dirname(spec_path), exist_ok=True)
            with open(spec_path, 'w') as f:
                f.write("---\nname: existing\ntype: module\n---\n")

            mock_provider = Mock()
            mock_provider.generate.return_value = """```yaml
components: []
build_order: []
```"""
            composer = SpecComposer(tmpdir, config=config, provider=mock_provider)

            composer.compose("Add to system")

            # Check that existing spec was passed in context
            call_args = mock_provider.generate.call_args[0][0]
            assert "existing" in call_args

    def test_generate_spec_content_formatting(self):
        """Test that spec content is properly generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_provider = Mock()
            mock_provider.generate.return_value = """---
name: auth
type: module
dependencies:
  - db
---

# Overview
Authentication module for the system
"""
            composer = SpecComposer(tmpdir, provider=mock_provider)

            comp = ComponentDef(
                name="auth",
                type="module",
                description="Auth service",
                dependencies=["db"]
            )
            arch = Architecture(
                components=[comp],
                dependencies={"auth": ["db"]},
                build_order=["db", "auth"],
                description="Auth system"
            )

            content = composer._generate_spec_content(comp, arch)
            assert "---" in content
            assert "name: auth" in content
            assert "type: module" in content

    def test_generate_spec_content_strips_markdown_fence(self):
        """Test that spec content strips markdown code fences."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_provider = Mock()
            # Return with markdown fence
            mock_provider.generate.return_value = """```markdown
---
name: test
type: function
---

# Overview
Test component
```"""
            composer = SpecComposer(tmpdir, provider=mock_provider)

            comp = ComponentDef(name="test", type="function", description="Test")
            arch = Architecture(components=[comp], dependencies={}, build_order=[])

            content = composer._generate_spec_content(comp, arch)
            assert not content.startswith("```")
            assert content.startswith("---")

    def test_architecture_build_order_with_dependencies(self):
        """Test that Architecture correctly captures dependencies."""
        yaml_str = """
components:
  - name: db
    type: module
    description: Database
    dependencies: []
  - name: auth
    type: module
    description: Authentication
    dependencies:
      - db
  - name: api
    type: module
    description: API
    dependencies:
      - db
      - auth
build_order:
  - db
  - auth
  - api
"""
        arch = Architecture.from_yaml(yaml_str)
        assert arch.dependencies["db"] == []
        assert arch.dependencies["auth"] == ["db"]
        assert arch.dependencies["api"] == ["db", "auth"]
        assert arch.build_order == ["db", "auth", "api"]
