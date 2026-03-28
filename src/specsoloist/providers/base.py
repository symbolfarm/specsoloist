"""Base protocol and types for LLM providers."""

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class LLMResponse:
    """Response from an LLM provider, including token usage metadata.

    Backward compatible: str() returns the text, so existing code
    that treats the response as a string continues to work.
    """

    text: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    model: Optional[str] = None

    def __str__(self) -> str:
        """Return the generated text for backward compatibility."""
        return self.text


class LLMProvider(Protocol):
    """Protocol defining the interface for LLM providers.

    Any LLM provider (Gemini, Anthropic, OpenAI, local models, etc.)
    must implement this interface to be used with SpecSoloist.
    """

    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        model: Optional[str] = None
    ) -> "LLMResponse":
        """Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM.
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
                        Default is 0.1 for consistent code generation.
            model: Optional model override. If None, uses the provider's default model.

        Returns:
            LLMResponse with generated text and optional token usage metadata.

        Raises:
            RuntimeError: If the API call fails.
        """
        ...
