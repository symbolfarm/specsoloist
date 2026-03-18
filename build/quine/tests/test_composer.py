"""Tests for the composer module."""

import os
import pytest
from unittest.mock import MagicMock

from specsoloist.config import SpecSoloistConfig
from spechestra.composer import Architecture, ComponentDef, CompositionResult, SpecComposer


ARCHITECTURE_YAML = """
description: A simple web app
components:
  - name: models
    type: bundle
    description: Data models
    dependencies: []
  - name: api
    type: bundle
    description: API handlers
    dependencies: [models]
dependencies:
  api: [models]
build_order: [models, api]
"""


class TestComponentDef:
    def test_default_creation(self):
        comp = ComponentDef(
            name="mycomp",
            type="bundle",
            description="A component",
        )
        assert comp.name == "mycomp"
        assert comp.inputs == {}
        assert comp.outputs == {}
        assert comp.dependencies == []

    def test_with_dependencies(self):
        comp = ComponentDef(
            name="api",
            type="bundle",
            description="API",
            dependencies=["models", "auth"],
        )
        assert comp.dependencies == ["models", "auth"]


class TestArchitecture:
    def test_default_creation(self):
        arch = Architecture()
        assert arch.components == []
        assert arch.dependencies == {}
        assert arch.build_order == []
        assert arch.description == ""

    def test_to_yaml(self):
        arch = Architecture(
            description="Test arch",
            components=[
                ComponentDef(name="foo", type="bundle", description="Foo component")
            ],
            build_order=["foo"],
        )
        yaml_str = arch.to_yaml()
        assert "foo" in yaml_str
        assert "description" in yaml_str

    def test_from_yaml_basic(self):
        arch = Architecture.from_yaml(ARCHITECTURE_YAML)
        assert len(arch.components) == 2
        assert arch.components[0].name == "models"
        assert arch.components[1].name == "api"

    def test_from_yaml_dependencies(self):
        arch = Architecture.from_yaml(ARCHITECTURE_YAML)
        assert "api" in arch.dependencies
        assert "models" in arch.dependencies["api"]

    def test_from_yaml_build_order(self):
        arch = Architecture.from_yaml(ARCHITECTURE_YAML)
        assert arch.build_order == ["models", "api"]

    def test_from_yaml_invalid_returns_empty(self):
        arch = Architecture.from_yaml("not valid yaml {{{{")
        assert isinstance(arch, Architecture)
        assert arch.components == []

    def test_from_yaml_wrong_type_returns_empty(self):
        arch = Architecture.from_yaml("- just a list\n- not a dict")
        assert isinstance(arch, Architecture)

    def test_round_trip(self):
        original = Architecture(
            description="Test",
            components=[
                ComponentDef(name="foo", type="bundle", description="Foo")
            ],
            build_order=["foo"],
        )
        yaml_str = original.to_yaml()
        restored = Architecture.from_yaml(yaml_str)
        assert len(restored.components) == 1
        assert restored.components[0].name == "foo"


class TestCompositionResult:
    def test_basic_creation(self):
        result = CompositionResult(
            architecture=Architecture(),
            spec_paths=["path/to/spec.spec.md"],
            ready_for_build=True,
        )
        assert result.ready_for_build is True
        assert result.cancelled is False

    def test_cancelled(self):
        result = CompositionResult(
            architecture=Architecture(),
            cancelled=True,
            ready_for_build=False,
        )
        assert result.cancelled is True


class TestSpecComposer:
    def test_init(self, tmp_path):
        config = SpecSoloistConfig(root_dir=str(tmp_path))
        composer = SpecComposer(str(tmp_path), config=config)
        assert os.path.isabs(composer.project_dir)

    def test_draft_architecture_calls_provider(self, tmp_path):
        config = SpecSoloistConfig(root_dir=str(tmp_path))
        mock_provider = MagicMock()
        mock_provider.generate.return_value = ARCHITECTURE_YAML
        composer = SpecComposer(str(tmp_path), config=config, provider=mock_provider)

        arch = composer.draft_architecture("Build a web app")
        assert mock_provider.generate.called
        assert isinstance(arch, Architecture)

    def test_draft_architecture_returns_empty_on_error(self, tmp_path):
        config = SpecSoloistConfig(root_dir=str(tmp_path))
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = Exception("LLM error")
        composer = SpecComposer(str(tmp_path), config=config, provider=mock_provider)

        arch = composer.draft_architecture("Build something")
        assert isinstance(arch, Architecture)
        assert arch.components == []

    def test_draft_architecture_with_context(self, tmp_path):
        config = SpecSoloistConfig(root_dir=str(tmp_path))
        mock_provider = MagicMock()
        mock_provider.generate.return_value = ARCHITECTURE_YAML
        composer = SpecComposer(str(tmp_path), config=config, provider=mock_provider)

        arch = composer.draft_architecture(
            "Build something",
            context={"existing_specs": ["auth", "users"]}
        )
        # Should include existing specs in prompt
        prompt = mock_provider.generate.call_args[0][0]
        assert "auth" in prompt or "users" in prompt

    def test_generate_specs_creates_files(self, tmp_path):
        src_dir = tmp_path / "specs"
        src_dir.mkdir()
        config = SpecSoloistConfig(root_dir=str(tmp_path), src_dir="specs")
        config.src_path = str(src_dir)

        mock_provider = MagicMock()
        mock_provider.generate.return_value = "---\nname: models\ntype: bundle\n---\n# Overview\nModels."
        composer = SpecComposer(str(tmp_path), config=config, provider=mock_provider)

        arch = Architecture(
            components=[
                ComponentDef(name="models", type="bundle", description="Data models")
            ]
        )

        paths = composer.generate_specs(arch)
        assert len(paths) == 1
        assert os.path.exists(paths[0])

    def test_generate_specs_skips_existing(self, tmp_path):
        src_dir = tmp_path / "specs"
        src_dir.mkdir()
        # Create existing spec
        (src_dir / "models.spec.md").write_text("---\nname: models\ntype: bundle\n---\n# Overview\nExisting.")

        config = SpecSoloistConfig(root_dir=str(tmp_path), src_dir="specs")
        config.src_path = str(src_dir)

        mock_provider = MagicMock()
        mock_provider.generate.return_value = "spec content"
        composer = SpecComposer(str(tmp_path), config=config, provider=mock_provider)

        arch = Architecture(
            components=[
                ComponentDef(name="models", type="bundle", description="Data models")
            ]
        )

        paths = composer.generate_specs(arch)
        # Should skip existing
        assert len(paths) == 0

    def test_compose_empty_architecture_cancelled(self, tmp_path):
        src_dir = tmp_path / "specs"
        src_dir.mkdir()
        config = SpecSoloistConfig(root_dir=str(tmp_path), src_dir="specs")
        config.src_path = str(src_dir)

        mock_provider = MagicMock()
        # Return empty/invalid architecture
        mock_provider.generate.return_value = "description: empty\ncomponents: []\nbuild_order: []"
        composer = SpecComposer(str(tmp_path), config=config, provider=mock_provider)

        result = composer.compose("Build nothing")
        assert result.cancelled is True
        assert result.ready_for_build is False

    def test_compose_returns_result_with_paths(self, tmp_path):
        src_dir = tmp_path / "specs"
        src_dir.mkdir()
        config = SpecSoloistConfig(root_dir=str(tmp_path), src_dir="specs")
        config.src_path = str(src_dir)

        mock_provider = MagicMock()
        # Return architecture first call, then spec content for generate_specs
        mock_provider.generate.side_effect = [
            ARCHITECTURE_YAML,
            "---\nname: models\ntype: bundle\n---\n# Overview\nModels.",
            "---\nname: api\ntype: bundle\n---\n# Overview\nAPI.",
        ]
        composer = SpecComposer(str(tmp_path), config=config, provider=mock_provider)

        result = composer.compose("Build a web app", auto_accept=True)
        assert isinstance(result, CompositionResult)
        assert result.ready_for_build is True
        assert len(result.spec_paths) > 0

    def test_compose_discovers_existing_specs(self, tmp_path):
        src_dir = tmp_path / "specs"
        src_dir.mkdir()
        (src_dir / "auth.spec.md").write_text("---\nname: auth\ntype: bundle\n---\n# Overview\nAuth.")

        config = SpecSoloistConfig(root_dir=str(tmp_path), src_dir="specs")
        config.src_path = str(src_dir)

        mock_provider = MagicMock()
        mock_provider.generate.return_value = "description: empty\ncomponents: []\nbuild_order: []"
        composer = SpecComposer(str(tmp_path), config=config, provider=mock_provider)

        composer.compose("Build something")
        prompt = mock_provider.generate.call_args[0][0]
        assert "auth" in prompt
