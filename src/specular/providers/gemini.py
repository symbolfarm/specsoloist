"""
Google Gemini LLM provider.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Optional


class GeminiProvider:
    """
    LLM provider for Google Gemini API.

    Uses urllib for HTTP requests to avoid external dependencies.
    """

    DEFAULT_MODEL = "gemini-2.0-flash"
    API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL
    ):
        """
        Initialize the Gemini provider.

        Args:
            api_key: Google AI API key. Falls back to GEMINI_API_KEY env var.
            model: Default model identifier (default: gemini-2.0-flash).
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY environment "
                "variable or pass api_key parameter."
            )

    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        model: Optional[str] = None
    ) -> str:
        """
        Generate a response from Gemini.

        Args:
            prompt: The prompt to send.
            temperature: Sampling temperature (0.0-1.0).
            model: Optional model override. If None, uses the default model.

        Returns:
            The generated text.

        Raises:
            RuntimeError: If the API call fails.
        """
        effective_model = model or self.model
        url = f"{self.API_BASE}/{effective_model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature}
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))

                try:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    return content
                except (KeyError, IndexError) as e:
                    raise RuntimeError(
                        f"Unexpected Gemini API response format: {result}"
                    ) from e

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise RuntimeError(
                f"Gemini API Error {e.code}: {e.reason}\nDetails: {error_body}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Error calling Gemini API: {str(e)}") from e
