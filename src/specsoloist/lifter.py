"""
SpecLifter - Reverse engineering source code into specs.
"""

import os
from typing import Optional

from .config import SpecSoloistConfig
from .providers import LLMProvider


class SpecLifter:
    """
    Reverse engineers Python source code into SpecSoloist specifications.
    """

    def __init__(
        self,
        config: Optional[SpecSoloistConfig] = None,
        provider: Optional[LLMProvider] = None
    ):
        self.config = config or SpecSoloistConfig.from_env()
        self.provider = provider or self.config.create_provider()

    def lift(
        self,
        source_path: str,
        test_path: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Generate a spec from source code.

        Args:
            source_path: Path to the python source file.
            test_path: Optional path to corresponding tests.
            model: Optional LLM model override.

        Returns:
            The generated spec content (Markdown).
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")

        with open(source_path, 'r') as f:
            source_code = f.read()

        test_code = ""
        if test_path and os.path.exists(test_path):
            with open(test_path, 'r') as f:
                content = f.read()
                test_code = f"\n\n# Existing Tests\n{content}"

        filename = os.path.basename(source_path)
        name = os.path.splitext(filename)[0]

        prompt = f"""You are a Reverse Engineering Specialist for the SpecSoloist framework.

Your task is to analyze Python source code and generate a rigorous "Spec-as-Source" Markdown specification for it.

# Input File: {filename}
```python
{source_code}
```
{test_code}

# Instructions
1. Analyze the code to understand its Interface, Behavior, Constraints, and Contract.
2. If tests are provided, extract scenarios from them.
3. Write a full `.spec.md` file that describes this component.
4. The output must be capable of regenerating the code with high fidelity.

# Spec Format
```markdown
---
name: {name}
type: [function|class|module]
status: draft
---

# Overview
[High-level summary]

# Interface
```yaml:schema
# Complete input/output schema or class definition
```

# Behavior
- [FR-01]: ...

# Constraints
- [NFR-01]: ...

# Contract
- Pre: ...
- Post: ...

# Examples
# Extract from tests or usage
```

# Output
Return ONLY the Markdown spec content. Start with `---`.
"""
        response = self.provider.generate(prompt, model=model)
        return self._clean_response(response)

    def _clean_response(self, response: str) -> str:
        """Strip Markdown code fences from the response if present."""
        content = response.strip()
        if content.startswith("```markdown"):
            content = content[11:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()
