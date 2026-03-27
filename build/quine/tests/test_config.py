"""Tests for the config module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from specsoloist.config import LanguageConfig, SpecSoloistConfig
from specsoloist.providers import (
    GeminiProvider,
    AnthropicProvider,
    PydanticAIProvider,
)


class TestLanguageConfig:
    """Tests for LanguageConfig dataclass."""

    def test_language_config_creation(self):
        """Test creating a LanguageConfig instance."""
        config = LanguageConfig(
            extension=".py",
            test_extension=".py",
            test_filename_pattern="test_{name}",
            test_command=["python", "-m", "pytest", "{file}"],
            env_vars={"PYTHONPATH": "{build_dir}"},
        )

        assert config.extension == ".py"
        assert config.test_extension == ".py"
        assert config.test_filename_pattern == "test_{name}"
        assert config.test_command == ["python", "-m", "pytest", "{file}"]
        assert config.env_vars == {"PYTHONPATH": "{build_dir}"}

    def test_language_config_no_env_vars(self):
        """Test LanguageConfig with default (empty) env_vars."""
        config = LanguageConfig(
            extension=".ts",
            test_extension=".ts",
            test_filename_pattern="{name}.test",
            test_command=["npx", "-y", "tsx", "{file}"],
        )

        assert config.env_vars == {}


class TestSpecSoloistConfig:
    """Tests for SpecSoloistConfig dataclass."""

    def test_default_configuration(self):
        """Test default SpecSoloistConfig values."""
        config = SpecSoloistConfig()

        assert config.llm_provider == "gemini"
        assert config.llm_model is None
        assert config.api_key is None
        assert config.root_dir == "."
        assert config.src_dir == "src"
        assert config.build_dir == "build"
        assert config.sandbox is False
        assert config.sandbox_image == "specsoloist-sandbox"

    def test_computed_paths(self):
        """Test that src_path and build_path are computed correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)

            # Paths should be absolute
            assert Path(config.src_path).is_absolute()
            assert Path(config.build_path).is_absolute()

            # Should be under the root directory
            assert config.src_path.startswith(tmpdir)
            assert config.build_path.startswith(tmpdir)

    def test_default_languages(self):
        """Test that default language configurations are provided."""
        config = SpecSoloistConfig()

        assert "python" in config.languages
        assert "typescript" in config.languages

        # Check Python config
        py_config = config.languages["python"]
        assert py_config.extension == ".py"
        assert py_config.test_extension == ".py"
        assert py_config.test_filename_pattern == "test_{name}"
        assert py_config.test_command == ["python", "-m", "pytest", "{file}"]
        assert py_config.env_vars == {"PYTHONPATH": "{build_dir}"}

        # Check TypeScript config
        ts_config = config.languages["typescript"]
        assert ts_config.extension == ".ts"
        assert ts_config.test_extension == ".ts"
        assert ts_config.test_filename_pattern == "{name}.test"
        assert ts_config.test_command == ["npx", "-y", "tsx", "{file}"]
        assert ts_config.env_vars == {}

    def test_custom_languages(self):
        """Test providing custom language configurations."""
        custom_lang = LanguageConfig(
            extension=".go",
            test_extension=".go",
            test_filename_pattern="{name}_test",
            test_command=["go", "test", "{file}"],
        )

        config = SpecSoloistConfig(languages={"go": custom_lang})

        assert "go" in config.languages
        assert config.languages["go"] == custom_lang

    def test_from_env_defaults(self):
        """Test from_env with no environment variables set."""
        with patch.dict(os.environ, {}, clear=True):
            config = SpecSoloistConfig.from_env()

            assert config.llm_provider == "gemini"
            assert config.llm_model is None
            assert config.api_key is None
            assert config.root_dir == "."
            assert config.src_dir == "src"
            assert config.sandbox is False
            # Note: from_env may use a different default than the class default,
            # so we just check it's set
            assert isinstance(config.sandbox_image, str)

    def test_from_env_with_provider(self):
        """Test from_env with custom provider."""
        with patch.dict(
            os.environ,
            {"SPECSOLOIST_LLM_PROVIDER": "anthropic"},
            clear=True,
        ):
            config = SpecSoloistConfig.from_env()
            assert config.llm_provider == "anthropic"

    def test_from_env_with_model(self):
        """Test from_env with custom model."""
        with patch.dict(
            os.environ,
            {"SPECSOLOIST_LLM_MODEL": "custom-model-123"},
            clear=True,
        ):
            config = SpecSoloistConfig.from_env()
            assert config.llm_model == "custom-model-123"

    def test_from_env_with_src_dir(self):
        """Test from_env with custom source directory."""
        with patch.dict(
            os.environ,
            {"SPECSOLOIST_SRC_DIR": "source"},
            clear=True,
        ):
            config = SpecSoloistConfig.from_env()
            assert config.src_dir == "source"

    def test_from_env_sandbox_enabled(self):
        """Test from_env with sandbox enabled."""
        with patch.dict(
            os.environ,
            {"SPECSOLOIST_SANDBOX": "true"},
            clear=True,
        ):
            config = SpecSoloistConfig.from_env()
            assert config.sandbox is True

    def test_from_env_sandbox_disabled_variants(self):
        """Test from_env with various false/disabled values for sandbox."""
        for value in ["false", "0", "no", "False", "FALSE"]:
            with patch.dict(
                os.environ,
                {"SPECSOLOIST_SANDBOX": value},
                clear=True,
            ):
                config = SpecSoloistConfig.from_env()
                assert config.sandbox is False

    def test_from_env_sandbox_image(self):
        """Test from_env with custom sandbox image."""
        with patch.dict(
            os.environ,
            {"SPECSOLOIST_SANDBOX_IMAGE": "custom-sandbox:v1"},
            clear=True,
        ):
            config = SpecSoloistConfig.from_env()
            assert config.sandbox_image == "custom-sandbox:v1"

    def test_from_env_gemini_api_key(self):
        """Test from_env loads GEMINI_API_KEY for gemini provider."""
        with patch.dict(
            os.environ,
            {
                "SPECSOLOIST_LLM_PROVIDER": "gemini",
                "GEMINI_API_KEY": "test-gemini-key",
            },
            clear=True,
        ):
            config = SpecSoloistConfig.from_env()
            assert config.api_key == "test-gemini-key"

    def test_from_env_google_api_key(self):
        """Test from_env loads GEMINI_API_KEY for google provider."""
        with patch.dict(
            os.environ,
            {
                "SPECSOLOIST_LLM_PROVIDER": "google",
                "GEMINI_API_KEY": "test-google-key",
            },
            clear=True,
        ):
            config = SpecSoloistConfig.from_env()
            assert config.api_key == "test-google-key"

    def test_from_env_anthropic_api_key(self):
        """Test from_env loads ANTHROPIC_API_KEY for anthropic provider."""
        with patch.dict(
            os.environ,
            {
                "SPECSOLOIST_LLM_PROVIDER": "anthropic",
                "ANTHROPIC_API_KEY": "test-anthropic-key",
            },
            clear=True,
        ):
            config = SpecSoloistConfig.from_env()
            assert config.api_key == "test-anthropic-key"

    def test_from_env_openai_api_key(self):
        """Test from_env loads OPENAI_API_KEY for openai provider."""
        with patch.dict(
            os.environ,
            {
                "SPECSOLOIST_LLM_PROVIDER": "openai",
                "OPENAI_API_KEY": "test-openai-key",
            },
            clear=True,
        ):
            config = SpecSoloistConfig.from_env()
            assert config.api_key == "test-openai-key"

    def test_from_env_openrouter_api_key(self):
        """Test from_env loads OPENROUTER_API_KEY for openrouter provider."""
        with patch.dict(
            os.environ,
            {
                "SPECSOLOIST_LLM_PROVIDER": "openrouter",
                "OPENROUTER_API_KEY": "test-openrouter-key",
            },
            clear=True,
        ):
            config = SpecSoloistConfig.from_env()
            assert config.api_key == "test-openrouter-key"

    def test_from_env_ollama_no_api_key(self):
        """Test from_env with ollama provider (no API key needed)."""
        with patch.dict(
            os.environ,
            {"SPECSOLOIST_LLM_PROVIDER": "ollama"},
            clear=True,
        ):
            config = SpecSoloistConfig.from_env()
            assert config.api_key is None

    def test_from_env_custom_root_dir(self):
        """Test from_env with custom root directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig.from_env(root_dir=tmpdir)
            assert config.root_dir == tmpdir

    def test_create_provider_gemini(self):
        """Test creating a Gemini provider."""
        config = SpecSoloistConfig(
            llm_provider="gemini", api_key="test-key"
        )
        provider = config.create_provider()

        assert isinstance(provider, GeminiProvider)

    def test_create_provider_gemini_with_model_no_override(self):
        """Test creating a Gemini provider without passing model override."""
        config = SpecSoloistConfig(
            llm_provider="gemini", api_key="test-key"
        )
        provider = config.create_provider()

        assert isinstance(provider, GeminiProvider)
        # Provider should use the passed api_key
        assert provider.api_key == "test-key"

    def test_create_provider_anthropic(self):
        """Test creating an Anthropic provider."""
        config = SpecSoloistConfig(
            llm_provider="anthropic", api_key="test-key"
        )
        provider = config.create_provider()

        assert isinstance(provider, AnthropicProvider)

    def test_create_provider_openai(self):
        """Test creating an OpenAI provider via PydanticAIProvider."""
        config = SpecSoloistConfig(
            llm_provider="openai", api_key="test-key"
        )
        provider = config.create_provider()

        assert isinstance(provider, PydanticAIProvider)
        assert provider.provider == "openai"

    def test_create_provider_openrouter(self):
        """Test creating an OpenRouter provider via PydanticAIProvider."""
        config = SpecSoloistConfig(
            llm_provider="openrouter", api_key="test-key"
        )
        provider = config.create_provider()

        assert isinstance(provider, PydanticAIProvider)
        assert provider.provider == "openrouter"

    def test_create_provider_ollama(self):
        """Test creating an Ollama provider via PydanticAIProvider."""
        config = SpecSoloistConfig(llm_provider="ollama")
        provider = config.create_provider()

        assert isinstance(provider, PydanticAIProvider)
        assert provider.provider == "ollama"

    def test_create_provider_google(self):
        """Test creating a Google provider via PydanticAIProvider."""
        config = SpecSoloistConfig(
            llm_provider="google", api_key="test-key"
        )
        provider = config.create_provider()

        assert isinstance(provider, PydanticAIProvider)
        assert provider.provider == "google"

    def test_create_provider_unknown(self):
        """Test that creating provider with unknown name raises ValueError."""
        config = SpecSoloistConfig(llm_provider="unknown-provider")

        with pytest.raises(ValueError) as exc_info:
            config.create_provider()

        assert "Unknown LLM provider" in str(exc_info.value)
        assert "unknown-provider" in str(exc_info.value)

    def test_create_provider_with_model_override(self):
        """Test creating a provider with custom model."""
        config = SpecSoloistConfig(
            llm_provider="gemini",
            llm_model="custom-model",
            api_key="test-key",
        )
        provider = config.create_provider()

        assert isinstance(provider, GeminiProvider)
        assert provider.model == "custom-model"

    def test_ensure_directories_creates_directories(self):
        """Test that ensure_directories creates src and build directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)

            # Directories should not exist yet
            assert not Path(config.src_path).exists()
            assert not Path(config.build_path).exists()

            config.ensure_directories()

            # After calling ensure_directories, they should exist
            assert Path(config.src_path).exists()
            assert Path(config.src_path).is_dir()
            assert Path(config.build_path).exists()
            assert Path(config.build_path).is_dir()

    def test_ensure_directories_idempotent(self):
        """Test that ensure_directories can be called multiple times safely."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)

            # Call multiple times
            config.ensure_directories()
            config.ensure_directories()
            config.ensure_directories()

            # Should still exist and be directories
            assert Path(config.src_path).is_dir()
            assert Path(config.build_path).is_dir()

    def test_ensure_directories_with_nested_paths(self):
        """Test ensure_directories with nested src/build directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(
                root_dir=tmpdir, src_dir="source/code", build_dir="out/build"
            )

            config.ensure_directories()

            assert Path(config.src_path).exists()
            assert Path(config.build_path).exists()

    def test_paths_are_absolute(self):
        """Test that src_path and build_path are always absolute."""
        config = SpecSoloistConfig(root_dir=".")

        assert Path(config.src_path).is_absolute()
        assert Path(config.build_path).is_absolute()

    def test_custom_configuration(self):
        """Test creating config with custom values."""
        custom_py = LanguageConfig(
            extension=".py",
            test_extension=".py",
            test_filename_pattern="test_{name}",
            test_command=["pytest", "{file}"],
            env_vars={"CUSTOM": "value"},
        )

        config = SpecSoloistConfig(
            llm_provider="anthropic",
            llm_model="claude-custom",
            api_key="custom-key",
            root_dir="/custom/root",
            src_dir="custom_src",
            build_dir="custom_build",
            sandbox=True,
            sandbox_image="custom:image",
            languages={"python": custom_py},
        )

        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-custom"
        assert config.api_key == "custom-key"
        assert config.root_dir == "/custom/root"
        assert config.src_dir == "custom_src"
        assert config.build_dir == "custom_build"
        assert config.sandbox is True
        assert config.sandbox_image == "custom:image"
        assert "python" in config.languages
