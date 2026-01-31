"""
Configuration management for Specular.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .providers import LLMProvider, GeminiProvider, AnthropicProvider


@dataclass
class LanguageConfig:
    """Configuration for a specific programming language."""
    extension: str
    test_extension: str
    test_filename_pattern: str  # e.g., "test_{name}" or "{name}.test"
    test_command: List[str]      # e.g., ["pytest", "{file}"]
    env_vars: Dict[str, str] = field(default_factory=dict)


@dataclass
class SpecSoloistConfig:
    """
    Configuration for SpecSoloist.

    Load order (later sources override earlier):
    1. Defaults (defined here)
    2. Environment variables
    3. Explicit constructor arguments
    """

    # LLM Configuration
    llm_provider: str = "gemini"  # "gemini" or "anthropic"
    llm_model: Optional[str] = None  # None = use provider default
    api_key: Optional[str] = None  # None = load from env

    # Directory Configuration
    root_dir: str = "."
    src_dir: str = "src"
    build_dir: str = "build"

    # Language Configuration
    languages: Dict[str, LanguageConfig] = field(default_factory=lambda: {
        "python": LanguageConfig(
            extension=".py",
            test_extension=".py",
            test_filename_pattern="test_{name}",
            test_command=["pytest", "{file}"],
            env_vars={"PYTHONPATH": "{build_dir}"}
        ),
        "typescript": LanguageConfig(
            extension=".ts",
            test_extension=".ts",
            test_filename_pattern="{name}.test",
            test_command=["npx", "-y", "tsx", "{file}"],
            env_vars={}
        )
    })

    # Computed paths (set in __post_init__)
    src_path: str = field(init=False, default="")
    build_path: str = field(init=False, default="")

    def __post_init__(self):
        """Compute absolute paths after initialization."""
        root = os.path.abspath(self.root_dir)
        self.src_path = os.path.join(root, self.src_dir)
        self.build_path = os.path.join(root, self.build_dir)

    @classmethod
    def from_env(cls, root_dir: str = ".") -> "SpecSoloistConfig":
        """
        Load configuration from environment variables.

        Environment variables:
            SPECSOLOIST_LLM_PROVIDER: "gemini" or "anthropic"
            SPECSOLOIST_LLM_MODEL: Model identifier
            GEMINI_API_KEY: API key for Gemini
            ANTHROPIC_API_KEY: API key for Anthropic
        """
        provider = os.environ.get("SPECSOLOIST_LLM_PROVIDER", "gemini")
        model = os.environ.get("SPECSOLOIST_LLM_MODEL")

        # Determine API key based on provider
        if provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        else:
            api_key = os.environ.get("GEMINI_API_KEY")

        return cls(
            root_dir=root_dir,
            llm_provider=provider,
            llm_model=model,
            api_key=api_key
        )

    def create_provider(self) -> LLMProvider:
        """
        Create an LLM provider instance based on configuration.

        Returns:
            An LLMProvider implementation.

        Raises:
            ValueError: If provider is unknown or API key is missing.
        """
        if self.llm_provider == "gemini":
            kwargs = {"api_key": self.api_key}
            if self.llm_model:
                kwargs["model"] = self.llm_model
            return GeminiProvider(**kwargs)

        elif self.llm_provider == "anthropic":
            kwargs = {"api_key": self.api_key}
            if self.llm_model:
                kwargs["model"] = self.llm_model
            return AnthropicProvider(**kwargs)

        else:
            raise ValueError(
                f"Unknown LLM provider: {self.llm_provider}. "
                "Supported: 'gemini', 'anthropic'"
            )

    def ensure_directories(self):
        """Create src and build directories if they don't exist."""
        os.makedirs(self.src_path, exist_ok=True)
        os.makedirs(self.build_path, exist_ok=True)
