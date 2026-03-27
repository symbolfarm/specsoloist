"""Pydantic AI LLM provider.

Supports Anthropic, OpenAI, Google Gemini, OpenRouter, and Ollama via the
pydantic-ai library's model-agnostic interface.

Requires: pydantic-ai-slim[anthropic,google,openai] (or pydantic-ai)
"""

import os
from typing import Optional


def _get_model_string(provider: str, model_name: str) -> str:
    """Map SpecSoloist provider/model config to a Pydantic AI model string.

    Args:
        provider: SpecSoloist provider name (anthropic, gemini, openai,
                  openrouter, ollama).
        model_name: Model identifier (e.g. "claude-sonnet-4-6",
                    "gemini-2.0-flash", "gpt-4o").

    Returns:
        A pydantic-ai model string (e.g. "anthropic:claude-sonnet-4-6").
    """
    provider = provider.lower()
    if provider == "anthropic":
        return f"anthropic:{model_name}"
    elif provider in ("gemini", "google"):
        return f"google-gla:{model_name}"
    elif provider == "openai":
        return f"openai:{model_name}"
    elif provider == "openrouter":
        # OpenRouter uses OpenAI-compatible API; handle in PydanticAIProvider
        return f"openai:{model_name}"
    elif provider == "ollama":
        return f"ollama:{model_name}"
    else:
        # Pass through for future providers or fully-qualified strings
        return model_name


class PydanticAIProvider:
    """LLM provider backed by pydantic-ai.

    Supports Anthropic, OpenAI, Google Gemini, OpenRouter, and Ollama.

    Provider strings recognized (SPECSOLOIST_LLM_PROVIDER):
        anthropic, gemini, google, openai, openrouter, ollama

    Relevant env vars:
        ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY,
        OPENROUTER_API_KEY, OLLAMA_BASE_URL (default: http://localhost:11434)
    """

    _DEFAULT_MODELS = {
        "anthropic": "claude-sonnet-4-20250514",
        "gemini": "gemini-2.0-flash",
        "google": "gemini-2.0-flash",
        "openai": "gpt-4o-mini",
        "openrouter": "anthropic/claude-3-haiku",
        "ollama": "llama3",
    }

    def __init__(
        self,
        provider: str = "gemini",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize the Pydantic AI provider.

        Args:
            provider: Provider name (anthropic, gemini, openai, openrouter, ollama).
            model: Default model identifier. Falls back to provider default.
            api_key: API key override. Falls back to appropriate env var.
        """
        self.provider = provider.lower()
        self.model = model or self._DEFAULT_MODELS.get(self.provider, "")
        self.api_key = api_key or self._get_default_api_key()

    def _get_default_api_key(self) -> Optional[str]:
        """Return the default API key for the configured provider."""
        if self.provider == "anthropic":
            return os.environ.get("ANTHROPIC_API_KEY")
        elif self.provider in ("gemini", "google"):
            return os.environ.get("GEMINI_API_KEY")
        elif self.provider == "openai":
            return os.environ.get("OPENAI_API_KEY")
        elif self.provider == "openrouter":
            return os.environ.get("OPENROUTER_API_KEY")
        # ollama: no key needed
        return None

    def _build_model(self, model_override: Optional[str] = None):
        """Build a pydantic-ai model object for the given (or default) model."""
        from pydantic_ai import Agent  # noqa: F401 — lazy import to keep startup fast
        effective_model_name = model_override or self.model

        if self.provider == "openrouter":
            from pydantic_ai.models.openai import OpenAIModel
            api_key = self.api_key or os.environ.get("OPENROUTER_API_KEY")
            return OpenAIModel(
                effective_model_name,
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
        elif self.provider == "ollama":
            from pydantic_ai.models.openai import OpenAIModel
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            return OpenAIModel(
                effective_model_name,
                base_url=f"{base_url}/v1",
                api_key="ollama",  # Ollama doesn't require a real key
            )
        else:
            model_str = _get_model_string(self.provider, effective_model_name)
            return model_str

    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        model: Optional[str] = None,
    ) -> str:
        """Generate a response using pydantic-ai.

        Args:
            prompt: The prompt to send to the LLM.
            temperature: Sampling temperature (0.0-1.0). Default 0.1.
            model: Optional model override.

        Returns:
            The generated text response.

        Raises:
            RuntimeError: If the API call fails or pydantic-ai is not installed.
        """
        try:
            from pydantic_ai import Agent
        except ImportError as e:
            raise RuntimeError(
                "pydantic-ai is required for this provider. "
                "Install with: pip install 'pydantic-ai-slim[anthropic,google,openai]'"
            ) from e

        try:
            model_obj = self._build_model(model)
            # Set API key env vars for providers that read from environment
            self._inject_api_key_env()
            agent = Agent(model_obj)
            result = agent.run_sync(prompt)
            return result.output
        except Exception as e:
            raise RuntimeError(
                f"Error calling {self.provider} via pydantic-ai: {e}"
            ) from e

    def _inject_api_key_env(self) -> None:
        """Set the appropriate API key env var if we have an explicit key."""
        if not self.api_key:
            return
        if self.provider == "anthropic":
            os.environ.setdefault("ANTHROPIC_API_KEY", self.api_key)
        elif self.provider in ("gemini", "google"):
            os.environ.setdefault("GEMINI_API_KEY", self.api_key)
            os.environ.setdefault("GOOGLE_API_KEY", self.api_key)
        elif self.provider == "openai":
            os.environ.setdefault("OPENAI_API_KEY", self.api_key)
        elif self.provider == "openrouter":
            os.environ.setdefault("OPENROUTER_API_KEY", self.api_key)
