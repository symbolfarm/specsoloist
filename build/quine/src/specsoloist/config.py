"""Configuration management for SpecSoloist."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    pass


@dataclass
class LanguageConfig:
    """Settings for building and testing in a specific programming language."""

    extension: str
    test_extension: str
    test_filename_pattern: str
    test_command: list[str]
    env_vars: Optional[dict[str, str]] = None


def _default_languages() -> dict[str, LanguageConfig]:
    """Return default language configurations."""
    return {
        "python": LanguageConfig(
            extension=".py",
            test_extension=".py",
            test_filename_pattern="test_{name}",
            test_command=["python", "-m", "pytest", "{file}"],
            env_vars={"PYTHONPATH": "{build_dir}"},
        ),
        "typescript": LanguageConfig(
            extension=".ts",
            test_extension=".ts",
            test_filename_pattern="{name}.test",
            test_command=["npx", "-y", "tsx", "{file}"],
            env_vars={},
        ),
    }


@dataclass
class SpecSoloistConfig:
    """Main configuration dataclass for the framework."""

    llm_provider: str = "gemini"
    llm_model: Optional[str] = None
    api_key: Optional[str] = None
    root_dir: str = "."
    src_dir: str = "src"
    build_dir: str = "build"
    sandbox: bool = False
    sandbox_image: str = "specsoloist-sandbox"
    languages: dict[str, LanguageConfig] = field(default_factory=_default_languages)
    src_path: str = field(init=False)
    build_path: str = field(init=False)

    def __post_init__(self) -> None:
        """Compute derived paths."""
        self.src_path = os.path.abspath(os.path.join(self.root_dir, self.src_dir))
        self.build_path = os.path.abspath(os.path.join(self.root_dir, self.build_dir))

    @classmethod
    def from_env(cls, root_dir: str = ".") -> "SpecSoloistConfig":
        """Load configuration from environment variables."""
        provider = os.environ.get("SPECSOLOIST_LLM_PROVIDER", "gemini")
        model = os.environ.get("SPECSOLOIST_LLM_MODEL")
        src_dir = os.environ.get("SPECSOLOIST_SRC_DIR", "src")
        sandbox = os.environ.get("SPECSOLOIST_SANDBOX", "").lower() == "true"
        sandbox_image = os.environ.get(
            "SPECSOLOIST_SANDBOX_IMAGE", "specsoloist-sandbox"
        )

        # Determine API key based on provider
        api_key = None
        if provider in ("gemini", "google"):
            api_key = os.environ.get("GEMINI_API_KEY")
        elif provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        elif provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
        elif provider == "openrouter":
            api_key = os.environ.get("OPENROUTER_API_KEY")
        # ollama: no API key required

        return cls(
            llm_provider=provider,
            llm_model=model if model else None,
            api_key=api_key,
            root_dir=root_dir,
            src_dir=src_dir,
            sandbox=sandbox,
            sandbox_image=sandbox_image,
        )

    def create_provider(self):
        """Create and return an LLM provider instance based on current config."""
        from specsoloist.providers import AnthropicProvider, GeminiProvider

        kwargs = {}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.llm_model:
            kwargs["model"] = self.llm_model

        if self.llm_provider == "gemini":
            return GeminiProvider(**kwargs)
        elif self.llm_provider == "anthropic":
            return AnthropicProvider(**kwargs)
        elif self.llm_provider in ("openai", "openrouter", "ollama", "google"):
            from specsoloist.providers import PydanticAIProvider

            return PydanticAIProvider(provider=self.llm_provider, **kwargs)
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider!r}")

    def ensure_directories(self) -> None:
        """Create src_path and build_path directories if they don't exist."""
        os.makedirs(self.src_path, exist_ok=True)
        os.makedirs(self.build_path, exist_ok=True)
