"""Configuration management for SpecSoloist."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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

    def create_provider(self, model_override: str | None = None):
        """Create and return an LLM provider instance based on configuration.

        Args:
            model_override: Optional model name to override the configured model.

        Returns:
            An instance of the appropriate LLM provider.

        Raises:
            ValueError: If the configured provider is not recognized.
        """
        # Determine which model to use
        model = model_override if model_override else self.llm_model

        # Validate provider
        valid_providers = ["anthropic", "gemini", "openai", "openrouter", "ollama", "google"]
        if self.llm_provider not in valid_providers:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")

        # Import and instantiate the appropriate provider
        if self.llm_provider == "anthropic":
            from specsoloist.providers.anthropic import AnthropicProvider
            return AnthropicProvider(api_key=self.api_key, model=model)
        elif self.llm_provider == "gemini":
            from specsoloist.providers.gemini import GeminiProvider
            return GeminiProvider(api_key=self.api_key, model=model)
        else:
            # For openai, openrouter, ollama, google - use PydanticAIProvider
            from specsoloist.providers.pydantic_ai_provider import PydanticAIProvider
            return PydanticAIProvider(provider=self.llm_provider, model=model, api_key=self.api_key)

    def ensure_directories(self):
        """Create src and build directories if they don't exist."""
        os.makedirs(self.src_path, exist_ok=True)
        os.makedirs(self.build_path, exist_ok=True)
