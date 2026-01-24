"""
Anthropic Claude LLM provider.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Optional


class AnthropicProvider:
    """
    LLM provider for Anthropic Claude API.

    Uses urllib for HTTP requests to avoid external dependencies.
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    API_BASE = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL
    ):
        """
        Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
            model: Model identifier (default: claude-sonnet-4-20250514).
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key parameter."
            )

    def generate(self, prompt: str, temperature: float = 0.1) -> str:
        """
        Generate a response from Claude.

        Args:
            prompt: The prompt to send.
            temperature: Sampling temperature (0.0-1.0).

        Returns:
            The generated text.

        Raises:
            RuntimeError: If the API call fails.
        """
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION
        }
        data = {
            "model": self.model,
            "max_tokens": 8192,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            req = urllib.request.Request(
                self.API_BASE,
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))

                try:
                    # Anthropic returns content as a list of content blocks
                    content_blocks = result['content']
                    # Extract text from all text blocks
                    text_parts = [
                        block['text']
                        for block in content_blocks
                        if block['type'] == 'text'
                    ]
                    return '\n'.join(text_parts)
                except (KeyError, IndexError) as e:
                    raise RuntimeError(
                        f"Unexpected Anthropic API response format: {result}"
                    ) from e

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise RuntimeError(
                f"Anthropic API Error {e.code}: {e.reason}\nDetails: {error_body}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Error calling Anthropic API: {str(e)}") from e
