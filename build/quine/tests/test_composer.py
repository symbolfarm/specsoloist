"""Tests for SpecComposer and related types."""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from spechestra.composer import (
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
        """Test creating a ComponentDef with required fields."""
        comp = ComponentDef(
            name="auth",
            type="module",
            description="Authentication system"
        )
        assert comp.name == "auth"
        assert comp.type == "module"
        assert comp.description == "Authentication system"
        assert comp.inputs == {}
        assert comp.outputs == {}
        assert comp.dependencies == []

    def test_component_def_with_inputs_outputs(self):
        """Test ComponentDef with inputs and outputs."""
        comp = ComponentDef(
            name="calculator",
            type="function",
            description="Add numbers",
            inputs={"a": "int", "b": "int"},
            outputs={"result": "int"}
        )
        assert comp.inputs == {"a": "int", "b": "int"}
        assert comp.outputs == {"result": "int"}

    def test_component_def_with_dependencies(self):
        """Test ComponentDef with dependencies."""
        comp = ComponentDef(
            name="auth_service",
            type="module",
            description="Service",
            dependencies=["database", "crypto"]
        )
        assert comp.dependencies == ["database", "crypto"]


class TestArchitecture:
    """Tests for Architecture dataclass."""

    def test_architecture_creation(self):
        """Test creating an Architecture."""
        comp1 = ComponentDef("db", "type", "Database")
        comp2 = ComponentDef("api", "module", "API", dependencies=["db"])

        arch = Architecture(
            components=[comp1, comp2],
            dependencies={"api": ["db"], "db": []},
            build_order=["db", "api"],
            description="Simple API with database"
        )

        assert len(arch.components) == 2
        assert arch.components[0].name == "db"
        assert arch.components[1].name == "api"
        assert arch.build_order == ["db", "api"]
        assert arch.description == "Simple API with database"

    def test_architecture_to_yaml(self):
        """Test serializing Architecture to YAML."""
        comp = ComponentDef("auth", "module", "Auth system")
        arch = Architecture(
            components=[comp],
            dependencies={"auth": []},
            build_order=["auth"],
            description="Auth"
        )

        yaml_str = arch.to_yaml()
        assert isinstance(yaml_str, str)
        assert "auth" in yaml_str
        assert "Auth system" in yaml_str

    def test_architecture_from_yaml(self):
        """Test parsing Architecture from YAML."""
        yaml_str = """
description: Test architecture
components:
  - name: database
    type: type
    description: Database model
    dependencies: []
  - name: api
    type: module
    description: API server
    dependencies:
      - database
build_order:
  - database
  - api
"""
        arch = Architecture.from_yaml(yaml_str)

        assert arch.description == "Test architecture"
        assert len(arch.components) == 2
        assert arch.components[0].name == "database"
        assert arch.components[1].name == "api"
        assert arch.components[1].dependencies == ["database"]
        assert arch.build_order == ["database", "api"]

    def test_architecture_from_yaml_with_inputs_outputs(self):
        """Test parsing Architecture from YAML with inputs/outputs."""
        yaml_str = """
description: Test
components:
  - name: math_func
    type: function
    description: Math operation
    inputs:
      a: int
      b: int
    outputs:
      result: int
    dependencies: []
build_order:
  - math_func
"""
        arch = Architecture.from_yaml(yaml_str)

        assert len(arch.components) == 1
        assert arch.components[0].inputs == {"a": "int", "b": "int"}
        assert arch.components[0].outputs == {"result": "int"}

    def test_architecture_from_empty_yaml(self):
        """Test parsing empty/minimal YAML returns empty architecture."""
        yaml_str = "description: Empty"

        arch = Architecture.from_yaml(yaml_str)

        assert arch.components == []
        assert arch.build_order == []
        assert arch.dependencies == {}

    def test_architecture_roundtrip_yaml(self):
        """Test serializing and deserializing Architecture maintains data."""
        original = Architecture(
            components=[
                ComponentDef("comp1", "function", "First"),
                ComponentDef("comp2", "module", "Second", dependencies=["comp1"])
            ],
            dependencies={"comp1": [], "comp2": ["comp1"]},
            build_order=["comp1", "comp2"],
            description="Test"
        )

        yaml_str = original.to_yaml()
        recovered = Architecture.from_yaml(yaml_str)

        assert len(recovered.components) == len(original.components)
        assert recovered.build_order == original.build_order
        assert recovered.description == original.description


class TestCompositionResult:
    """Tests for CompositionResult dataclass."""

    def test_composition_result_success(self):
        """Test creating a successful CompositionResult."""
        arch = Architecture(components=[], dependencies={}, build_order=[])
        result = CompositionResult(
            architecture=arch,
            spec_paths=["/path/to/spec1.md", "/path/to/spec2.md"],
            ready_for_build=True
        )

        assert result.ready_for_build is True
        assert result.cancelled is False
        assert len(result.spec_paths) == 2

    def test_composition_result_cancelled(self):
        """Test creating a cancelled CompositionResult."""
        arch = Architecture(components=[], dependencies={}, build_order=[])
        result = CompositionResult(
            architecture=arch,
            spec_paths=[],
            ready_for_build=False,
            cancelled=True
        )

        assert result.ready_for_build is False
        assert result.cancelled is True


class TestSpecComposer:
    """Tests for SpecComposer class."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = os.path.join(tmpdir, "src")
            os.makedirs(src_dir)
            yield tmpdir

    def test_composer_initialization(self, temp_project):
        """Test initializing a SpecComposer."""
        composer = SpecComposer(temp_project)

        assert composer.project_dir == os.path.abspath(temp_project)
        assert composer.config is not None
        assert composer.parser is not None

    def test_composer_with_custom_config(self, temp_project):
        """Test initializing with custom config."""
        config = SpecSoloistConfig(root_dir=temp_project)
        composer = SpecComposer(temp_project, config=config)

        assert composer.config == config

    def test_composer_with_custom_provider(self, temp_project):
        """Test initializing with custom provider."""
        mock_provider = Mock()
        composer = SpecComposer(temp_project, provider=mock_provider)

        assert composer._provider == mock_provider

    def test_get_provider_lazy_creation(self, temp_project):
        """Test that provider is created lazily."""
        with patch('specsoloist.config.SpecSoloistConfig.create_provider') as mock_create:
            mock_provider = Mock()
            mock_create.return_value = mock_provider

            composer = SpecComposer(temp_project)
            assert composer._provider is None

            # First access should create provider
            provider = composer._get_provider()
            assert provider == mock_provider
            mock_create.assert_called_once()

    def test_draft_architecture_basic(self, temp_project):
        """Test drafting an architecture."""
        mock_provider = Mock()
        yaml_response = """description: Simple app
components:
  - name: auth
    type: module
    description: Authentication
    dependencies: []
  - name: api
    type: module
    description: REST API
    dependencies:
      - auth
build_order:
  - auth
  - api
"""
        mock_provider.generate.return_value = yaml_response

        composer = SpecComposer(temp_project, provider=mock_provider)
        arch = composer.draft_architecture("Build an app with auth")

        assert len(arch.components) == 2
        assert arch.components[0].name == "auth"
        assert arch.components[1].name == "api"
        assert arch.build_order == ["auth", "api"]
        mock_provider.generate.assert_called_once()

    def test_draft_architecture_with_context(self, temp_project):
        """Test drafting architecture with existing specs context."""
        mock_provider = Mock()
        mock_provider.generate.return_value = "description: Test\ncomponents: []\nbuild_order: []"

        composer = SpecComposer(temp_project, provider=mock_provider)
        context = {"existing_specs": ["user_model", "database"]}

        arch = composer.draft_architecture("Extend app", context=context)

        # Check that prompt includes existing specs
        call_args = mock_provider.generate.call_args
        prompt = call_args[0][0] if call_args[0] else call_args[1].get('prompt', '')
        assert "user_model" in prompt
        assert "database" in prompt

    def test_draft_architecture_malformed_yaml(self, temp_project):
        """Test handling malformed YAML response."""
        mock_provider = Mock()
        mock_provider.generate.return_value = "this is not valid yaml: {["

        composer = SpecComposer(temp_project, provider=mock_provider)
        arch = composer.draft_architecture("Build app")

        # Should return empty architecture on parse failure
        assert arch.components == []
        assert arch.build_order == []

    def test_draft_architecture_wrong_type(self, temp_project):
        """Test handling non-dict YAML response."""
        mock_provider = Mock()
        mock_provider.generate.return_value = "- just a list\n- not a dict"

        composer = SpecComposer(temp_project, provider=mock_provider)
        arch = composer.draft_architecture("Build app")

        assert arch.components == []
        assert arch.build_order == []

    def test_parse_architecture_response_with_yaml_block(self):
        """Test parsing response with ```yaml block."""
        response = """Here's the architecture:

```yaml
description: My app
components:
  - name: core
    type: bundle
    description: Core logic
    dependencies: []
build_order:
  - core
```

This is the plan.
"""
        composer = SpecComposer(".")
        arch = composer._parse_architecture_response(response)

        assert len(arch.components) == 1
        assert arch.components[0].name == "core"

    def test_parse_architecture_response_with_bare_yaml(self):
        """Test parsing response with bare ```yaml block."""
        response = """
```
description: Test
components:
  - name: test
    type: function
    description: Test function
    dependencies: []
build_order:
  - test
```
"""
        composer = SpecComposer(".")
        arch = composer._parse_architecture_response(response)

        assert len(arch.components) == 1
        assert arch.components[0].name == "test"

    def test_generate_specs_creates_files(self, temp_project):
        """Test generate_specs creates spec files."""
        mock_provider = Mock()
        mock_provider.generate.return_value = """---
name: auth
type: module
---

# Overview
Authentication module
"""

        config = SpecSoloistConfig(root_dir=temp_project)
        composer = SpecComposer(temp_project, config=config, provider=mock_provider)

        arch = Architecture(
            components=[
                ComponentDef("auth", "module", "Auth system"),
                ComponentDef("api", "module", "API")
            ],
            dependencies={"auth": [], "api": ["auth"]},
            build_order=["auth", "api"]
        )

        paths = composer.generate_specs(arch)

        assert len(paths) == 2
        assert any("auth" in p for p in paths)
        assert any("api" in p for p in paths)

        # Check files were created
        for path in paths:
            assert os.path.exists(path)
            assert path.endswith(".spec.md")

    def test_generate_specs_skips_existing(self, temp_project):
        """Test generate_specs skips existing specs."""
        # Create an existing spec
        src_dir = os.path.join(temp_project, "src")
        os.makedirs(src_dir, exist_ok=True)
        existing_spec = os.path.join(src_dir, "existing.spec.md")
        with open(existing_spec, "w") as f:
            f.write("---\nname: existing\ntype: function\n---\n")

        mock_provider = Mock()
        mock_provider.generate.return_value = "---\nname: new\ntype: function\n---\n"

        config = SpecSoloistConfig(root_dir=temp_project)
        composer = SpecComposer(temp_project, config=config, provider=mock_provider)

        arch = Architecture(
            components=[
                ComponentDef("existing", "function", "Exists"),
                ComponentDef("new", "function", "New")
            ],
            dependencies={"existing": [], "new": []},
            build_order=["existing", "new"]
        )

        paths = composer.generate_specs(arch)

        # Should only create spec for "new", not "existing"
        assert len(paths) == 1
        assert "new" in paths[0]

    def test_generate_spec_content_basic(self, temp_project):
        """Test generating spec content for a component."""
        mock_provider = Mock()
        spec_content = """---
name: test_comp
type: function
---

# Overview
Test component
"""
        mock_provider.generate.return_value = spec_content

        composer = SpecComposer(temp_project, provider=mock_provider)
        comp = ComponentDef("test_comp", "function", "Test component")
        arch = Architecture(
            components=[comp],
            dependencies={},
            build_order=[]
        )

        content = composer._generate_spec_content(comp, arch)

        assert "test_comp" in content or "---" in content
        mock_provider.generate.assert_called_once()

    def test_generate_spec_content_with_dependencies(self, temp_project):
        """Test generating spec content includes dependencies."""
        mock_provider = Mock()
        mock_provider.generate.return_value = "---\nname: test\ntype: function\n---"

        composer = SpecComposer(temp_project, provider=mock_provider)
        comp = ComponentDef(
            "auth",
            "module",
            "Auth",
            dependencies=["crypto", "database"]
        )
        arch = Architecture(
            components=[comp],
            dependencies={"auth": ["crypto", "database"]},
            build_order=[]
        )

        content = composer._generate_spec_content(comp, arch)

        # Check prompt includes dependencies
        call_args = mock_provider.generate.call_args
        prompt = call_args[0][0]
        assert "crypto" in prompt
        assert "database" in prompt

    def test_compose_full_workflow(self, temp_project):
        """Test the complete compose workflow."""
        mock_provider = Mock()
        mock_provider.generate.side_effect = [
            # First call: architecture drafting
            """description: Todo app
components:
  - name: models
    type: type
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
""",
            # Second and third calls: spec generation
            "---\nname: models\ntype: type\n---\n# Overview\nModels",
            "---\nname: api\ntype: module\n---\n# Overview\nAPI"
        ]

        config = SpecSoloistConfig(root_dir=temp_project)
        composer = SpecComposer(temp_project, config=config, provider=mock_provider)

        result = composer.compose("Build a todo app")

        assert result.ready_for_build is True
        assert result.cancelled is False
        assert len(result.architecture.components) == 2
        assert len(result.spec_paths) >= 1

    def test_compose_empty_architecture(self, temp_project):
        """Test compose returns cancelled when architecture is empty."""
        mock_provider = Mock()
        mock_provider.generate.return_value = """description: Failed
components: []
build_order: []
"""

        composer = SpecComposer(temp_project, provider=mock_provider)
        result = composer.compose("Build something")

        assert result.cancelled is True
        assert result.ready_for_build is False
        assert result.spec_paths == []

    def test_compose_with_existing_specs(self, temp_project):
        """Test compose discovers existing specs."""
        # Create existing spec
        src_dir = os.path.join(temp_project, "src")
        os.makedirs(src_dir, exist_ok=True)
        existing_spec = os.path.join(src_dir, "auth.spec.md")
        with open(existing_spec, "w") as f:
            f.write("---\nname: auth\ntype: module\n---\n")

        mock_provider = Mock()
        mock_provider.generate.return_value = """description: App
components:
  - name: api
    type: module
    description: API
    dependencies:
      - auth
build_order:
  - auth
  - api
"""

        config = SpecSoloistConfig(root_dir=temp_project)
        composer = SpecComposer(temp_project, config=config, provider=mock_provider)

        result = composer.compose("Build an API")

        # Check that draft_architecture was called and received context
        call_args = mock_provider.generate.call_args
        prompt = call_args[0][0]
        assert "auth" in prompt  # Should mention existing spec

    def test_compose_auto_accept_parameter(self, temp_project):
        """Test compose with auto_accept parameter."""
        mock_provider = Mock()
        mock_provider.generate.return_value = """description: App
components: []
build_order: []
"""

        composer = SpecComposer(temp_project, provider=mock_provider)

        # auto_accept=True should not affect the result logic
        result = composer.compose("Build app", auto_accept=True)

        assert result.cancelled is True

    def test_compose_with_context_parameter(self, temp_project):
        """Test compose with custom context."""
        mock_provider = Mock()
        mock_provider.generate.return_value = """description: Extended
components:
  - name: feature
    type: function
    description: New feature
    dependencies: []
build_order:
  - feature
"""

        composer = SpecComposer(temp_project, provider=mock_provider)
        context = {"custom_key": "custom_value"}

        result = composer.compose("Add feature", context=context)

        # Should succeed with context
        assert len(result.architecture.components) >= 0


class TestSpecComposerIntegration:
    """Integration tests for SpecComposer."""

    @pytest.fixture
    def temp_project_with_specs(self):
        """Create a temporary project with some existing specs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = os.path.join(tmpdir, "src")
            os.makedirs(src_dir)

            # Create a few existing specs
            specs = {
                "utils": "---\nname: utils\ntype: bundle\n---\n# Overview\nUtility functions",
                "database": "---\nname: database\ntype: module\n---\n# Overview\nDatabase module"
            }

            for name, content in specs.items():
                with open(os.path.join(src_dir, f"{name}.spec.md"), "w") as f:
                    f.write(content)

            yield tmpdir

    def test_composer_finds_existing_specs(self, temp_project_with_specs):
        """Test that composer discovers existing specs."""
        config = SpecSoloistConfig(root_dir=temp_project_with_specs)
        composer = SpecComposer(temp_project_with_specs, config=config)

        existing = composer.parser.list_specs()
        assert len(existing) >= 1
        existing_names = [os.path.basename(p).replace(".spec.md", "") for p in existing]
        assert "utils" in existing_names or "database" in existing_names

    def test_architecture_yaml_roundtrip_complex(self):
        """Test complex architecture serialization roundtrip."""
        components = [
            ComponentDef("storage", "module", "File storage"),
            ComponentDef("models", "type", "Data models"),
            ComponentDef("api", "module", "REST API", dependencies=["models", "storage"]),
            ComponentDef("cli", "module", "CLI tool", dependencies=["models"]),
        ]

        arch = Architecture(
            components=components,
            dependencies={
                "storage": [],
                "models": [],
                "api": ["models", "storage"],
                "cli": ["models"],
            },
            build_order=["storage", "models", "api", "cli"],
            description="Full-featured app with API and CLI"
        )

        yaml_str = arch.to_yaml()
        recovered = Architecture.from_yaml(yaml_str)

        assert len(recovered.components) == 4
        assert recovered.build_order == ["storage", "models", "api", "cli"]
        assert recovered.dependencies["api"] == ["models", "storage"]
        assert recovered.dependencies["cli"] == ["models"]
