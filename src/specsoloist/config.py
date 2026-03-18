"""Configuration management for SpecSoloist."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .providers import LLMProvider, GeminiProvider, AnthropicProvider, PydanticAIProvider


@dataclass
class LanguageConfig:
    """Settings for building and testing in a specific language."""
    extension: str
    test_extension: str
    test_filename_pattern: str
    test_command: List[str]
    env_vars: Dict[str, str] = field(default_factory=dict)


@dataclass
class SpecSoloistConfig:
    """Main configuration for the SpecSoloist framework."""

    llm_provider: str = "gemini"
    llm_model: Optional[str] = None
    api_key: Optional[str] = None
    root_dir: str = "."
    src_dir: str = "src"
    build_dir: str = "build"
    sandbox: bool = False
    sandbox_image: str = "specsoloist-sandbox"

    languages: Dict[str, LanguageConfig] = field(default_factory=lambda: {
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
    })

    src_path: str = field(init=False, default="")
    build_path: str = field(init=False, default="")

    def __post_init__(self):
        """Compute derived absolute paths from root_dir."""
        root = os.path.abspath(self.root_dir)
        self.src_path = os.path.join(root, self.src_dir)
        self.build_path = os.path.join(root, self.build_dir)

    @classmethod
    def from_env(cls, root_dir: str = ".") -> "SpecSoloistConfig":
        """Load configuration from environment variables."""
        provider = os.environ.get("SPECSOLOIST_LLM_PROVIDER", "gemini")
        model = os.environ.get("SPECSOLOIST_LLM_MODEL")
        src_dir = os.environ.get("SPECSOLOIST_SRC_DIR", "src")
        sandbox = os.environ.get("SPECSOLOIST_SANDBOX", "false").lower() == "true"
        sandbox_image = os.environ.get("SPECSOLOIST_SANDBOX_IMAGE", "python:3.11-slim")

        if provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        elif provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
        elif provider == "openrouter":
            api_key = os.environ.get("OPENROUTER_API_KEY")
        elif provider == "ollama":
            api_key = None  # Ollama doesn't require an API key
        else:
            api_key = os.environ.get("GEMINI_API_KEY")

        return cls(
            root_dir=root_dir,
            llm_provider=provider,
            llm_model=model,
            src_dir=src_dir,
            api_key=api_key,
            sandbox=sandbox,
            sandbox_image=sandbox_image,
        )

    def create_provider(self) -> LLMProvider:
        """Create an LLM provider instance based on current config."""
        kwargs = {"api_key": self.api_key}
        if self.llm_model:
            kwargs["model"] = self.llm_model

        if self.llm_provider == "gemini":
            return GeminiProvider(**kwargs)
        elif self.llm_provider == "anthropic":
            return AnthropicProvider(**kwargs)
        elif self.llm_provider in ("openai", "openrouter", "ollama", "google"):
            # New providers backed by pydantic-ai
            return PydanticAIProvider(provider=self.llm_provider, **kwargs)
        else:
            raise ValueError(
                f"Unknown LLM provider: {self.llm_provider}. "
                "Supported: 'gemini', 'anthropic', 'openai', 'openrouter', 'ollama'"
            )

    def ensure_directories(self):
        """Create src and build directories if they don't exist."""
        os.makedirs(self.src_path, exist_ok=True)
        os.makedirs(self.build_path, exist_ok=True)
