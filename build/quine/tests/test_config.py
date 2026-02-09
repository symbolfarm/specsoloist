"""
Tests for config module.
"""

import pytest
import os
import shutil
import tempfile
from specsoloist.config import LanguageConfig, SpecSoloistConfig


@pytest.fixture
def temp_dir():
    """Create and clean up a temporary directory."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)


class TestLanguageConfig:
    """Tests for LanguageConfig dataclass."""

    def test_language_config_python(self):
        """Test Python language configuration."""
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

    def test_language_config_typescript(self):
        """Test TypeScript language configuration."""
        config = LanguageConfig(
            extension=".ts",
            test_extension=".ts",
            test_filename_pattern="{name}.test",
            test_command=["npx", "-y", "tsx", "{file}"],
            env_vars={},
        )
        assert config.extension == ".ts"
        assert config.test_extension == ".ts"
        assert config.test_filename_pattern == "{name}.test"
        assert config.test_command == ["npx", "-y", "tsx", "{file}"]
        assert config.env_vars == {}

    def test_language_config_custom(self):
        """Test custom language configuration."""
        config = LanguageConfig(
            extension=".go",
            test_extension=".go",
            test_filename_pattern="{name}_test",
            test_command=["go", "test", "{file}"],
            env_vars={"GO_ENV": "test"},
        )
        assert config.extension == ".go"
        assert config.test_filename_pattern == "{name}_test"
        assert config.env_vars == {"GO_ENV": "test"}

    def test_language_config_default_env_vars(self):
        """Test that env_vars defaults to empty dict."""
        config = LanguageConfig(
            extension=".py",
            test_extension=".py",
            test_filename_pattern="test_{name}",
            test_command=["python", "-m", "pytest", "{file}"],
        )
        assert config.env_vars == {}


class TestSpecSoloistConfigDefaults:
    """Tests for SpecSoloistConfig default values."""

    def test_default_llm_provider(self):
        """Test default LLM provider is gemini."""
        config = SpecSoloistConfig()
        assert config.llm_provider == "gemini"

    def test_default_llm_model(self):
        """Test default LLM model is None."""
        config = SpecSoloistConfig()
        assert config.llm_model is None

    def test_default_api_key(self):
        """Test default API key is None."""
        config = SpecSoloistConfig()
        assert config.api_key is None

    def test_default_root_dir(self):
        """Test default root directory is current directory."""
        config = SpecSoloistConfig()
        assert config.root_dir == "."

    def test_default_src_dir(self):
        """Test default source directory is 'src'."""
        config = SpecSoloistConfig()
        assert config.src_dir == "src"

    def test_default_build_dir(self):
        """Test default build directory is 'build'."""
        config = SpecSoloistConfig()
        assert config.build_dir == "build"

    def test_default_languages(self):
        """Test default languages include Python and TypeScript."""
        config = SpecSoloistConfig()
        assert "python" in config.languages
        assert "typescript" in config.languages

    def test_default_python_config(self):
        """Test default Python language configuration."""
        config = SpecSoloistConfig()
        py_config = config.languages["python"]
        assert py_config.extension == ".py"
        assert py_config.test_extension == ".py"
        assert py_config.test_filename_pattern == "test_{name}"
        assert py_config.test_command == ["python", "-m", "pytest", "{file}"]
        assert py_config.env_vars == {"PYTHONPATH": "{build_dir}"}

    def test_default_typescript_config(self):
        """Test default TypeScript language configuration."""
        config = SpecSoloistConfig()
        ts_config = config.languages["typescript"]
        assert ts_config.extension == ".ts"
        assert ts_config.test_extension == ".ts"
        assert ts_config.test_filename_pattern == "{name}.test"
        assert ts_config.test_command == ["npx", "-y", "tsx", "{file}"]
        assert ts_config.env_vars == {}


class TestSpecSoloistConfigPaths:
    """Tests for computed path properties."""

    def test_src_path_computed_absolute(self, temp_dir):
        """Test that src_path is computed as absolute path."""
        config = SpecSoloistConfig(root_dir=temp_dir)
        expected = os.path.join(os.path.abspath(temp_dir), "src")
        assert config.src_path == expected

    def test_build_path_computed_absolute(self, temp_dir):
        """Test that build_path is computed as absolute path."""
        config = SpecSoloistConfig(root_dir=temp_dir)
        expected = os.path.join(os.path.abspath(temp_dir), "build")
        assert config.build_path == expected

    def test_src_path_custom_dir(self, temp_dir):
        """Test src_path with custom source directory."""
        config = SpecSoloistConfig(root_dir=temp_dir, src_dir="source")
        expected = os.path.join(os.path.abspath(temp_dir), "source")
        assert config.src_path == expected

    def test_build_path_custom_dir(self, temp_dir):
        """Test build_path with custom build directory."""
        config = SpecSoloistConfig(root_dir=temp_dir, build_dir="dist")
        expected = os.path.join(os.path.abspath(temp_dir), "dist")
        assert config.build_path == expected

    def test_paths_are_absolute(self):
        """Test that computed paths are always absolute."""
        config = SpecSoloistConfig(root_dir="relative/path")
        assert os.path.isabs(config.src_path)
        assert os.path.isabs(config.build_path)


class TestSpecSoloistConfigInit:
    """Tests for configuration initialization."""

    def test_init_with_all_args(self, temp_dir):
        """Test initialization with all arguments."""
        config = SpecSoloistConfig(
            llm_provider="anthropic",
            llm_model="claude-opus",
            api_key="test-key",
            root_dir=temp_dir,
            src_dir="source",
            build_dir="output",
        )
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-opus"
        assert config.api_key == "test-key"
        assert config.root_dir == temp_dir
        assert config.src_dir == "source"
        assert config.build_dir == "output"

    def test_init_partial_args(self):
        """Test initialization with partial arguments."""
        config = SpecSoloistConfig(
            llm_provider="anthropic",
            llm_model="claude-3-sonnet",
        )
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3-sonnet"
        assert config.api_key is None
        assert config.root_dir == "."

    def test_init_preserves_languages(self):
        """Test that languages dict is preserved during init."""
        config = SpecSoloistConfig()
        original_python = config.languages["python"]

        config2 = SpecSoloistConfig()
        assert config2.languages["python"].extension == original_python.extension


class TestSpecSoloistConfigFromEnv:
    """Tests for from_env class method."""

    def test_from_env_default_provider(self, monkeypatch, temp_dir):
        """Test from_env defaults to gemini provider."""
        monkeypatch.delenv("SPECSOLOIST_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("SPECSOLOIST_LLM_MODEL", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        config = SpecSoloistConfig.from_env(root_dir=temp_dir)
        assert config.llm_provider == "gemini"

    def test_from_env_gemini_provider(self, monkeypatch, temp_dir):
        """Test from_env with explicit gemini provider."""
        monkeypatch.setenv("SPECSOLOIST_LLM_PROVIDER", "gemini")
        monkeypatch.setenv("GEMINI_API_KEY", "gemini-key-123")

        config = SpecSoloistConfig.from_env(root_dir=temp_dir)
        assert config.llm_provider == "gemini"
        assert config.api_key == "gemini-key-123"

    def test_from_env_anthropic_provider(self, monkeypatch, temp_dir):
        """Test from_env with anthropic provider."""
        monkeypatch.setenv("SPECSOLOIST_LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key-456")

        config = SpecSoloistConfig.from_env(root_dir=temp_dir)
        assert config.llm_provider == "anthropic"
        assert config.api_key == "anthropic-key-456"

    def test_from_env_gemini_api_key_ignored_for_anthropic(self, monkeypatch, temp_dir):
        """Test that GEMINI_API_KEY is ignored when provider is anthropic."""
        monkeypatch.setenv("SPECSOLOIST_LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("GEMINI_API_KEY", "gemini-key-123")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key-456")

        config = SpecSoloistConfig.from_env(root_dir=temp_dir)
        assert config.api_key == "anthropic-key-456"

    def test_from_env_model(self, monkeypatch, temp_dir):
        """Test from_env loads LLM model."""
        monkeypatch.setenv("SPECSOLOIST_LLM_MODEL", "claude-opus-4")

        config = SpecSoloistConfig.from_env(root_dir=temp_dir)
        assert config.llm_model == "claude-opus-4"

    def test_from_env_src_dir(self, monkeypatch, temp_dir):
        """Test from_env loads custom source directory."""
        monkeypatch.setenv("SPECSOLOIST_SRC_DIR", "source")

        config = SpecSoloistConfig.from_env(root_dir=temp_dir)
        assert config.src_dir == "source"

    def test_from_env_default_src_dir(self, monkeypatch, temp_dir):
        """Test from_env defaults to 'src' for source directory."""
        monkeypatch.delenv("SPECSOLOIST_SRC_DIR", raising=False)

        config = SpecSoloistConfig.from_env(root_dir=temp_dir)
        assert config.src_dir == "src"

    def test_from_env_no_api_key(self, monkeypatch, temp_dir):
        """Test from_env when no API key is set."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        config = SpecSoloistConfig.from_env(root_dir=temp_dir)
        assert config.api_key is None

    def test_from_env_multiple_vars(self, monkeypatch, temp_dir):
        """Test from_env with multiple environment variables set."""
        monkeypatch.setenv("SPECSOLOIST_LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("SPECSOLOIST_LLM_MODEL", "claude-opus-4")
        monkeypatch.setenv("SPECSOLOIST_SRC_DIR", "my_src")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "key-xyz")

        config = SpecSoloistConfig.from_env(root_dir=temp_dir)
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-opus-4"
        assert config.src_dir == "my_src"
        assert config.api_key == "key-xyz"


class TestSpecSoloistConfigCreateProvider:
    """Tests for create_provider method."""

    def test_create_gemini_provider(self):
        """Test creating a Gemini provider."""
        config = SpecSoloistConfig(
            llm_provider="gemini",
            api_key="test-key",
        )
        provider = config.create_provider()
        assert provider is not None
        # Verify it's a GeminiProvider by checking it has the generate method
        assert hasattr(provider, "generate")
        assert callable(provider.generate)

    def test_create_anthropic_provider(self):
        """Test creating an Anthropic provider."""
        config = SpecSoloistConfig(
            llm_provider="anthropic",
            api_key="test-key",
        )
        provider = config.create_provider()
        assert provider is not None
        assert hasattr(provider, "generate")
        assert callable(provider.generate)

    def test_create_provider_with_model(self):
        """Test creating a provider with explicit model."""
        config = SpecSoloistConfig(
            llm_provider="gemini",
            llm_model="gemini-pro",
            api_key="test-key",
        )
        provider = config.create_provider()
        assert provider is not None

    def test_create_provider_without_model(self):
        """Test creating a provider without explicit model uses default."""
        config = SpecSoloistConfig(
            llm_provider="gemini",
            api_key="test-key",
        )
        provider = config.create_provider()
        assert provider is not None

    def test_create_provider_without_api_key(self, monkeypatch):
        """Test creating a provider without explicit API key but from environment."""
        monkeypatch.setenv("GEMINI_API_KEY", "env-key")
        config = SpecSoloistConfig(
            llm_provider="gemini",
            api_key=None,
        )
        # Should use environment variable
        provider = config.create_provider()
        assert provider is not None

    def test_create_provider_unknown_provider(self):
        """Test that unknown provider raises ValueError."""
        config = SpecSoloistConfig(llm_provider="unknown")
        with pytest.raises(ValueError) as exc_info:
            config.create_provider()
        assert "Unknown LLM provider" in str(exc_info.value)
        assert "unknown" in str(exc_info.value)

    def test_create_provider_case_sensitive(self):
        """Test that provider name is case sensitive."""
        config = SpecSoloistConfig(llm_provider="Gemini")
        with pytest.raises(ValueError):
            config.create_provider()


class TestSpecSoloistConfigEnsureDirectories:
    """Tests for ensure_directories method."""

    def test_ensure_directories_creates_both(self, temp_dir):
        """Test that ensure_directories creates both src and build directories."""
        config = SpecSoloistConfig(root_dir=temp_dir)
        config.ensure_directories()

        assert os.path.exists(config.src_path)
        assert os.path.exists(config.build_path)
        assert os.path.isdir(config.src_path)
        assert os.path.isdir(config.build_path)

    def test_ensure_directories_idempotent(self, temp_dir):
        """Test that ensure_directories can be called multiple times safely."""
        config = SpecSoloistConfig(root_dir=temp_dir)
        config.ensure_directories()
        config.ensure_directories()  # Should not raise

        assert os.path.exists(config.src_path)
        assert os.path.exists(config.build_path)

    def test_ensure_directories_custom_names(self, temp_dir):
        """Test ensure_directories with custom directory names."""
        config = SpecSoloistConfig(
            root_dir=temp_dir,
            src_dir="source",
            build_dir="output",
        )
        config.ensure_directories()

        assert os.path.exists(config.src_path)
        assert os.path.exists(config.build_path)
        assert config.src_path.endswith("source")
        assert config.build_path.endswith("output")

    def test_ensure_directories_creates_nested_structure(self, temp_dir):
        """Test ensure_directories creates nested directory structure."""
        nested_temp = os.path.join(temp_dir, "nested", "deep")
        config = SpecSoloistConfig(root_dir=nested_temp)
        config.ensure_directories()

        assert os.path.exists(config.src_path)
        assert os.path.exists(config.build_path)

    def test_ensure_directories_existing_src_only(self, temp_dir):
        """Test ensure_directories when src already exists."""
        os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)

        config = SpecSoloistConfig(root_dir=temp_dir)
        config.ensure_directories()

        assert os.path.exists(config.src_path)
        assert os.path.exists(config.build_path)

    def test_ensure_directories_preserves_existing_files(self, temp_dir):
        """Test that ensure_directories doesn't remove existing files."""
        os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)
        test_file = os.path.join(temp_dir, "src", "test.py")
        with open(test_file, "w") as f:
            f.write("# test")

        config = SpecSoloistConfig(root_dir=temp_dir)
        config.ensure_directories()

        assert os.path.exists(test_file)
        with open(test_file, "r") as f:
            assert f.read() == "# test"


class TestSpecSoloistConfigIntegration:
    """Integration tests for SpecSoloistConfig."""

    def test_full_workflow(self, temp_dir, monkeypatch):
        """Test complete configuration workflow."""
        monkeypatch.setenv("SPECSOLOIST_LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        config = SpecSoloistConfig.from_env(root_dir=temp_dir)
        config.ensure_directories()

        assert config.llm_provider == "anthropic"
        assert config.api_key == "test-key"
        assert os.path.exists(config.src_path)
        assert os.path.exists(config.build_path)

    def test_provider_creation_after_from_env(self, monkeypatch):
        """Test that provider can be created after from_env."""
        monkeypatch.setenv("SPECSOLOIST_LLM_PROVIDER", "gemini")
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        config = SpecSoloistConfig.from_env()
        provider = config.create_provider()
        assert provider is not None

    def test_custom_language_support(self, temp_dir):
        """Test adding custom language configuration."""
        config = SpecSoloistConfig(root_dir=temp_dir)

        # Add a custom language
        config.languages["go"] = LanguageConfig(
            extension=".go",
            test_extension=".go",
            test_filename_pattern="{name}_test",
            test_command=["go", "test", "{file}"],
            env_vars={},
        )

        assert "go" in config.languages
        assert config.languages["go"].extension == ".go"
