"""Tests for the config module."""

import os
import pytest
from unittest.mock import patch

from specsoloist.config import LanguageConfig, SpecSoloistConfig


class TestLanguageConfig:
    def test_python_config(self):
        cfg = LanguageConfig(
            extension=".py",
            test_extension=".py",
            test_filename_pattern="test_{name}",
            test_command=["python", "-m", "pytest", "{file}"],
            env_vars={"PYTHONPATH": "{build_dir}"},
        )
        assert cfg.extension == ".py"
        assert cfg.test_filename_pattern == "test_{name}"

    def test_typescript_config(self):
        cfg = LanguageConfig(
            extension=".ts",
            test_extension=".ts",
            test_filename_pattern="{name}.test",
            test_command=["npx", "-y", "tsx", "{file}"],
            env_vars={},
        )
        assert cfg.extension == ".ts"
        assert cfg.test_filename_pattern == "{name}.test"


class TestSpecSoloistConfig:
    def test_defaults(self):
        cfg = SpecSoloistConfig()
        assert cfg.llm_provider == "gemini"
        assert cfg.llm_model is None
        assert cfg.src_dir == "src"
        assert cfg.build_dir == "build"
        assert cfg.sandbox is False
        assert cfg.sandbox_image == "specsoloist-sandbox"

    def test_computed_paths(self):
        cfg = SpecSoloistConfig(root_dir="/tmp/project")
        assert cfg.src_path == "/tmp/project/src"
        assert cfg.build_path == "/tmp/project/build"

    def test_computed_paths_custom_dirs(self):
        cfg = SpecSoloistConfig(root_dir="/tmp/project", src_dir="source", build_dir="output")
        assert cfg.src_path == "/tmp/project/source"
        assert cfg.build_path == "/tmp/project/output"

    def test_default_languages_include_python(self):
        cfg = SpecSoloistConfig()
        assert "python" in cfg.languages
        assert cfg.languages["python"].extension == ".py"

    def test_default_languages_include_typescript(self):
        cfg = SpecSoloistConfig()
        assert "typescript" in cfg.languages
        assert cfg.languages["typescript"].extension == ".ts"

    def test_from_env_defaults(self):
        with patch.dict(os.environ, {}, clear=False):
            # Remove env vars that might affect defaults
            env_to_clear = [
                "SPECSOLOIST_LLM_PROVIDER", "SPECSOLOIST_LLM_MODEL",
                "SPECSOLOIST_SRC_DIR", "SPECSOLOIST_SANDBOX"
            ]
            env_backup = {}
            for key in env_to_clear:
                env_backup[key] = os.environ.pop(key, None)

            try:
                cfg = SpecSoloistConfig.from_env()
                assert cfg.llm_provider == "gemini"
                assert cfg.src_dir == "src"
                assert cfg.sandbox is False
            finally:
                for key, val in env_backup.items():
                    if val is not None:
                        os.environ[key] = val

    def test_from_env_custom_provider(self):
        with patch.dict(os.environ, {"SPECSOLOIST_LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "test-key"}):
            cfg = SpecSoloistConfig.from_env()
            assert cfg.llm_provider == "anthropic"
            assert cfg.api_key == "test-key"

    def test_from_env_gemini_api_key(self):
        with patch.dict(os.environ, {
            "SPECSOLOIST_LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "gemini-key-123"
        }):
            cfg = SpecSoloistConfig.from_env()
            assert cfg.api_key == "gemini-key-123"

    def test_from_env_sandbox(self):
        with patch.dict(os.environ, {"SPECSOLOIST_SANDBOX": "true"}):
            cfg = SpecSoloistConfig.from_env()
            assert cfg.sandbox is True

    def test_from_env_sandbox_false(self):
        with patch.dict(os.environ, {"SPECSOLOIST_SANDBOX": "false"}):
            cfg = SpecSoloistConfig.from_env()
            assert cfg.sandbox is False

    def test_create_provider_unknown_raises(self):
        cfg = SpecSoloistConfig(llm_provider="unknown_provider")
        with pytest.raises((ValueError, ImportError)):
            cfg.create_provider()

    def test_ensure_directories(self, tmp_path):
        cfg = SpecSoloistConfig(root_dir=str(tmp_path))
        cfg.ensure_directories()
        assert os.path.isdir(cfg.src_path)
        assert os.path.isdir(cfg.build_path)
