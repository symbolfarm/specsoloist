"""
Tests for PydanticAIProvider — model string mapping, config integration,
and provider initialization (task 20).
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from specsoloist.providers.pydantic_ai_provider import (
    PydanticAIProvider,
    _get_model_string,
)
from specsoloist.config import SpecSoloistConfig


# ---------------------------------------------------------------------------
# _get_model_string mapping
# ---------------------------------------------------------------------------

class TestGetModelString:
    def test_anthropic_maps_correctly(self):
        assert _get_model_string("anthropic", "claude-3-haiku") == "anthropic:claude-3-haiku"

    def test_gemini_maps_correctly(self):
        assert _get_model_string("gemini", "gemini-2.0-flash") == "google-gla:gemini-2.0-flash"

    def test_google_maps_correctly(self):
        assert _get_model_string("google", "gemini-pro") == "google-gla:gemini-pro"

    def test_openai_maps_correctly(self):
        assert _get_model_string("openai", "gpt-4o") == "openai:gpt-4o"

    def test_openrouter_maps_to_openai_prefix(self):
        # OpenRouter uses OpenAI-compat; the model string gets "openai:" prefix
        result = _get_model_string("openrouter", "anthropic/claude-3-haiku")
        assert result == "openai:anthropic/claude-3-haiku"

    def test_ollama_maps_correctly(self):
        assert _get_model_string("ollama", "llama3") == "ollama:llama3"

    def test_unknown_provider_passthrough(self):
        assert _get_model_string("custom", "my-model") == "my-model"

    def test_case_insensitive(self):
        assert _get_model_string("ANTHROPIC", "claude") == "anthropic:claude"
        assert _get_model_string("Gemini", "flash") == "google-gla:flash"


# ---------------------------------------------------------------------------
# PydanticAIProvider initialization
# ---------------------------------------------------------------------------

class TestPydanticAIProviderInit:
    def test_default_provider_is_gemini(self):
        p = PydanticAIProvider()
        assert p.provider == "gemini"

    def test_provider_stored_lowercased(self):
        p = PydanticAIProvider(provider="Anthropic")
        assert p.provider == "anthropic"

    def test_model_stored(self):
        p = PydanticAIProvider(provider="anthropic", model="claude-3-haiku")
        assert p.model == "claude-3-haiku"

    def test_default_model_for_anthropic(self):
        p = PydanticAIProvider(provider="anthropic")
        assert "claude" in p.model.lower()

    def test_default_model_for_gemini(self):
        p = PydanticAIProvider(provider="gemini")
        assert "gemini" in p.model.lower()

    def test_default_model_for_openai(self):
        p = PydanticAIProvider(provider="openai")
        assert "gpt" in p.model.lower() or p.model  # has a default

    def test_api_key_explicit(self):
        p = PydanticAIProvider(provider="anthropic", api_key="sk-test")
        assert p.api_key == "sk-test"

    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
        p = PydanticAIProvider(provider="anthropic")
        assert p.api_key == "env-key"

    def test_ollama_has_no_api_key_requirement(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        p = PydanticAIProvider(provider="ollama")
        # No key required — api_key may be None
        assert p.provider == "ollama"


# ---------------------------------------------------------------------------
# Config integration
# ---------------------------------------------------------------------------

class TestConfigPydanticAIIntegration:
    def _make_config(self, provider, key_env=None, monkeypatch=None):
        if monkeypatch and key_env:
            for k, v in key_env.items():
                monkeypatch.setenv(k, v)
        return SpecSoloistConfig(
            root_dir="/tmp",
            llm_provider=provider,
            llm_model="test-model",
        )

    def test_openai_provider_creates_pydantic_ai_provider(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        config = self._make_config("openai")
        provider = config.create_provider()
        assert isinstance(provider, PydanticAIProvider)
        assert provider.provider == "openai"

    def test_openrouter_provider_creates_pydantic_ai_provider(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")
        config = self._make_config("openrouter")
        provider = config.create_provider()
        assert isinstance(provider, PydanticAIProvider)
        assert provider.provider == "openrouter"

    def test_ollama_provider_creates_pydantic_ai_provider(self):
        config = SpecSoloistConfig(
            root_dir="/tmp",
            llm_provider="ollama",
            api_key=None,
        )
        provider = config.create_provider()
        assert isinstance(provider, PydanticAIProvider)
        assert provider.provider == "ollama"

    def test_unknown_provider_raises_value_error(self):
        config = SpecSoloistConfig(
            root_dir="/tmp",
            llm_provider="unknown-provider",
            api_key="key",
        )
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            config.create_provider()

    def test_gemini_still_creates_gemini_provider(self, monkeypatch):
        from specsoloist.providers import GeminiProvider
        monkeypatch.setenv("GEMINI_API_KEY", "gk-test")
        config = self._make_config("gemini")
        provider = config.create_provider()
        assert isinstance(provider, GeminiProvider)

    def test_anthropic_still_creates_anthropic_provider(self, monkeypatch):
        from specsoloist.providers import AnthropicProvider
        monkeypatch.setenv("ANTHROPIC_API_KEY", "ak-test")
        config = self._make_config("anthropic")
        provider = config.create_provider()
        assert isinstance(provider, AnthropicProvider)


# ---------------------------------------------------------------------------
# from_env: new provider env vars
# ---------------------------------------------------------------------------

class TestFromEnvNewProviders:
    def test_openai_reads_openai_api_key(self, monkeypatch):
        monkeypatch.setenv("SPECSOLOIST_LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        config = SpecSoloistConfig.from_env("/tmp")
        assert config.llm_provider == "openai"
        assert config.api_key == "sk-test"

    def test_openrouter_reads_openrouter_api_key(self, monkeypatch):
        monkeypatch.setenv("SPECSOLOIST_LLM_PROVIDER", "openrouter")
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")
        config = SpecSoloistConfig.from_env("/tmp")
        assert config.llm_provider == "openrouter"
        assert config.api_key == "or-test"

    def test_ollama_has_no_api_key(self, monkeypatch):
        monkeypatch.setenv("SPECSOLOIST_LLM_PROVIDER", "ollama")
        config = SpecSoloistConfig.from_env("/tmp")
        assert config.llm_provider == "ollama"
        assert config.api_key is None


# ---------------------------------------------------------------------------
# generate() with mocked pydantic-ai (unit test — no real API calls)
# ---------------------------------------------------------------------------

class TestPydanticAIProviderGenerate:
    def test_generate_returns_agent_output(self, monkeypatch):
        """generate() calls pydantic-ai Agent and returns result.output."""
        mock_result = MagicMock()
        mock_result.output = "Generated code here"

        mock_agent_instance = MagicMock()
        mock_agent_instance.run_sync.return_value = mock_result

        mock_agent_class = MagicMock(return_value=mock_agent_instance)

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        p = PydanticAIProvider(provider="anthropic", model="claude-test", api_key="sk-test")

        with patch("specsoloist.providers.pydantic_ai_provider.PydanticAIProvider._build_model",
                   return_value="anthropic:claude-test"), \
             patch("pydantic_ai.Agent", mock_agent_class):
            result = p.generate("Write some code")

        assert str(result) == "Generated code here"
        assert result.text == "Generated code here"
        mock_agent_instance.run_sync.assert_called_once_with("Write some code")
