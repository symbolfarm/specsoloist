"""
Configuration management for SpecSoloist.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .providers import LLMProvider, GeminiProvider, AnthropicProvider


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
        root = os.path.abspath(self.root_dir)
        self.src_path = os.path.join(root, self.src_dir)
        self.build_path = os.path.join(root, self.build_dir)

    @classmethod
    def from_env(cls, root_dir: str = ".") -> "SpecSoloistConfig":
        """Load configuration from environment variables."""
        provider = os.environ.get("SPECSOLOIST_LLM_PROVIDER", "gemini")
        model = os.environ.get("SPECSOLOIST_LLM_MODEL")
        src_dir = os.environ.get("SPECSOLOIST_SRC_DIR", "src")

        if provider == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        else:
            api_key = os.environ.get("GEMINI_API_KEY")

        return cls(
            root_dir=root_dir,
            llm_provider=provider,
            llm_model=model,
            src_dir=src_dir,
            api_key=api_key,
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
        else:
            raise ValueError(
                f"Unknown LLM provider: {self.llm_provider}. "
                "Supported: 'gemini', 'anthropic'"
            )

    def ensure_directories(self):
        """Create src and build directories if they don't exist."""
        os.makedirs(self.src_path, exist_ok=True)
        os.makedirs(self.build_path, exist_ok=True)
