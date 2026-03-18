"""Reverse-engineers source code into SpecSoloist specifications."""

from __future__ import annotations

import os
import re
from typing import Optional

from specsoloist.config import SpecSoloistConfig


def _strip_fences(text: str) -> str:
    """Strip markdown code fences from response."""
    text = re.sub(r"^```[a-zA-Z]*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n```\s*$", "", text.strip())
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


class Respecer:
    """Reverse engineering tool for generating specs from source code."""

    def __init__(
        self,
        config: Optional[SpecSoloistConfig] = None,
        provider=None,
    ) -> None:
        self.config = config or SpecSoloistConfig.from_env()
        self.provider = provider or self.config.create_provider()

    def respec(
        self,
        source_path: str,
        test_path: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """Generate a spec from source code."""
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")

        with open(source_path) as f:
            source_code = f.read()

        # Load spec format rules if available
        spec_format_rules = ""
        spec_format_path = os.path.join(
            self.config.root_dir, "score", "spec_format.spec.md"
        )
        if os.path.exists(spec_format_path):
            with open(spec_format_path) as f:
                spec_format_rules = f.read()

        # Load test context if provided
        test_context = ""
        if test_path and os.path.exists(test_path):
            with open(test_path) as f:
                test_context = f.read()

        # Build the prompt
        parts = []

        if spec_format_rules:
            parts.append(
                f"## Spec Format Rules\n{spec_format_rules}"
            )

        parts.append(f"## Source Code\n```\n{source_code}\n```")

        if test_context:
            parts.append(f"## Tests\n```\n{test_context}\n```")

        parts.append(
            "Analyze the above source code and produce a requirements-oriented spec "
            "in the SpecSoloist format. Focus on WHAT the code does (public API, "
            "behavior, edge cases, examples), not HOW it does it. "
            "Write the spec as a .spec.md file with proper YAML frontmatter."
        )

        prompt = "\n\n".join(parts)
        response = self.provider.generate(prompt, model=model)
        return _strip_fences(response)
