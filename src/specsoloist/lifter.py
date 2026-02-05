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
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")

        with open(source_path, 'r') as f:
            source_code = f.read()

        # Load the Spec Format definition to give the LLM the "Gold Standard"
        spec_format_path = os.path.join(self.config.root_dir, "self_hosting/spec_format.spec.md")
        spec_rules = ""
        if os.path.exists(spec_format_path):
            with open(spec_format_path, 'r') as f:
                spec_rules = f"\n# Spec Format Rules\n{f.read()}"

        test_code = ""
        if test_path and os.path.exists(test_path):
            with open(test_path, 'r') as f:
                content = f.read()
                test_code = f"\n\n# Existing Tests\n{content}"

        filename = os.path.basename(source_path)

        prompt = f"""You are a Senior Software Architect and Reverse Engineering Specialist.

Your task is to analyze Python source code and generate a rigorous "Spec-as-Source" Markdown specification for it.

# Goal
The generated spec must be of such high fidelity that the SpecSoloist compiler can use it to regenerate the original code (or a functionally identical, idiomatic version) that passes all existing tests.

{spec_rules}

# Input File: {filename}
```python
{source_code}
```
{test_code}

# Instructions
1. **Analyze**: Understand the Interface (inputs/outputs), Behavior (FRs), and Design Contract (pre/post).
2. **Decompose**: If the file is monolithic (contains many unrelated classes/functions), suggest how to break it into multiple specs in the "Overview".
3. **Rigorous Schema**: Use the `yaml:schema` block (or `yaml:functions`/`yaml:types` for bundles) as defined in the rules.
4. **Test Awareness**: Use the provided test code to extract concrete Examples.
5. **No implementation details**: Focus on *what* the code does, not the internal Python logic, unless it's a specific constraint.

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
