"""
Base protocol for LLM providers.
"""

from typing import Optional, Protocol


class LLMProvider(Protocol):
    """
    Protocol defining the interface for LLM providers.

    Any LLM provider (Gemini, Anthropic, OpenAI, local models, etc.)
    must implement this interface to be used with Specular.
    """

    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        model: Optional[str] = None
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM.
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
                        Default is 0.1 for consistent code generation.
            model: Optional model override. If None, uses the provider's default model.

        Returns:
            The generated text response.

        Raises:
            RuntimeError: If the API call fails.
        """
        ...
