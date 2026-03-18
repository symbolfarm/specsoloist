"""Tests for the respec module."""

import os
import pytest
from unittest.mock import MagicMock, patch

from specsoloist.config import SpecSoloistConfig
from specsoloist.respec import Respecer


class MockProvider:
    def __init__(self, response="---\nname: generated_spec\ntype: bundle\n---\n# Overview\nGenerated."):
        self.response = response
        self.calls = []

    def generate(self, prompt, model=None):
        self.calls.append({"prompt": prompt, "model": model})
        return self.response


@pytest.fixture
def source_file(tmp_path):
    f = tmp_path / "mymodule.py"
    f.write_text("def add(a, b):\n    return a + b\n")
    return str(f)


@pytest.fixture
def test_file(tmp_path):
    f = tmp_path / "test_mymodule.py"
    f.write_text("def test_add():\n    assert add(1, 2) == 3\n")
    return str(f)


class TestRespecer:
    def test_init_with_provider(self):
        provider = MockProvider()
        config = SpecSoloistConfig()
        respecer = Respecer(config=config, provider=provider)
        assert respecer.provider is provider

    def test_respec_missing_source_raises(self, tmp_path):
        provider = MockProvider()
        config = SpecSoloistConfig()
        respecer = Respecer(config=config, provider=provider)
        with pytest.raises(FileNotFoundError):
            respecer.respec(str(tmp_path / "nonexistent.py"))

    def test_respec_returns_string(self, source_file):
        provider = MockProvider()
        config = SpecSoloistConfig()
        respecer = Respecer(config=config, provider=provider)
        result = respecer.respec(source_file)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_respec_includes_source_in_prompt(self, source_file):
        provider = MockProvider()
        config = SpecSoloistConfig()
        respecer = Respecer(config=config, provider=provider)
        respecer.respec(source_file)
        prompt = provider.calls[0]["prompt"]
        assert "def add" in prompt

    def test_respec_with_test_context(self, source_file, test_file):
        provider = MockProvider()
        config = SpecSoloistConfig()
        respecer = Respecer(config=config, provider=provider)
        respecer.respec(source_file, test_path=test_file)
        prompt = provider.calls[0]["prompt"]
        assert "def test_add" in prompt

    def test_respec_without_test_context(self, source_file, tmp_path):
        provider = MockProvider()
        config = SpecSoloistConfig()
        respecer = Respecer(config=config, provider=provider)
        # Passing nonexistent test path should not error
        respecer.respec(source_file, test_path=str(tmp_path / "nonexistent.py"))
        assert len(provider.calls) == 1

    def test_respec_passes_model(self, source_file):
        provider = MockProvider()
        config = SpecSoloistConfig()
        respecer = Respecer(config=config, provider=provider)
        respecer.respec(source_file, model="claude-haiku")
        assert provider.calls[0]["model"] == "claude-haiku"

    def test_respec_strips_fences(self, source_file):
        provider = MockProvider("```markdown\n---\nname: myspec\n---\n```")
        config = SpecSoloistConfig()
        respecer = Respecer(config=config, provider=provider)
        result = respecer.respec(source_file)
        assert "```" not in result

    def test_respec_loads_spec_format_if_present(self, tmp_path):
        source = tmp_path / "mymod.py"
        source.write_text("x = 1\n")

        # Create a score/spec_format.spec.md
        score_dir = tmp_path / "score"
        score_dir.mkdir()
        spec_format = score_dir / "spec_format.spec.md"
        spec_format.write_text("# Spec Format Rules\nFollow these rules.")

        config = SpecSoloistConfig(root_dir=str(tmp_path))
        provider = MockProvider()
        respecer = Respecer(config=config, provider=provider)
        respecer.respec(str(source))
        prompt = provider.calls[0]["prompt"]
        assert "Spec Format Rules" in prompt
