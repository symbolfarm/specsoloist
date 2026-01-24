"""
Spec compilation: prompt construction and code generation.
"""

import re
from typing import Protocol

from .parser import ParsedSpec


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    def generate(self, prompt: str, temperature: float = 0.1) -> str:
        """Generate a response from the LLM."""
        ...


class SpecCompiler:
    """Compiles specs to code using an LLM provider."""

    def __init__(self, provider: LLMProvider, global_context: str = ""):
        self.provider = provider
        self.global_context = global_context

    def compile_code(self, spec: ParsedSpec) -> str:
        """Compiles a spec to implementation code."""
        language = spec.metadata.language_target

        prompt = f"""
You are an expert {language} developer.
Your task is to implement the code described in the following specification.

# Global Project Context
{self.global_context}

# Component Specification
{spec.body}

# Instructions
1. Implement the component exactly as described in the Functional Requirements.
2. Adhere strictly to the Non-Functional Requirements (Performance, Purity).
3. Ensure the code satisfies the Design Contract (Pre/Post-conditions).
4. Output ONLY the raw code for the implementation. Do not wrap in markdown code blocks.
"""
        code = self.provider.generate(prompt)
        return self._strip_markdown_fences(code)

    def compile_tests(self, spec: ParsedSpec) -> str:
        """Generates a test suite for a spec."""
        language = spec.metadata.language_target
        module_name = spec.metadata.name or spec.path.replace(".spec.md", "")

        prompt = f"""
You are an expert QA Engineer specialized in {language}.
Your task is to write a comprehensive unit test suite for the component described below.

# Component Specification
{spec.body}

# Instructions
1. Write a standard test file (e.g., using `pytest` for Python).
2. The component implementation will be in a module named `{module_name}`. Import it like `from {module_name} import ...`.
3. Implement a test case for EVERY scenario listed in the 'Test Scenarios' section of the spec.
4. Implement additional edge cases based on the 'Design Contract' (Pre/Post-conditions).
5. Output ONLY the raw code.
"""
        code = self.provider.generate(prompt)
        return self._strip_markdown_fences(code)

    def generate_fix(
        self,
        spec: ParsedSpec,
        code_content: str,
        test_content: str,
        error_log: str
    ) -> str:
        """
        Generates a fix for failing tests.
        Returns the raw LLM response with FILE markers.
        """
        module_name = spec.metadata.name or spec.path.replace(".spec.md", "")

        prompt = f"""
You are a Senior Software Engineer tasked with fixing a build failure.
Analyze the discrepancy between the Code, the Test, and the Specification.

# 1. The Specification (Source of Truth)
{spec.content}

# 2. The Current Implementation ({module_name}.py)
{code_content}

# 3. The Failing Test Suite (test_{module_name}.py)
{test_content}

# 4. The Test Failure Output
{error_log}

# Instructions
1. Analyze why the test failed.
2. Determine if the **Code** is buggy (violates spec) or if the **Test** is wrong (hallucinated expectation).
3. Provide the CORRECTED content for the file that needs fixing.
4. Use the following format for your output so I can apply the patch:

### FILE: build/{module_name}.py
... (full corrected code content) ...
### END

OR

### FILE: build/test_{module_name}.py
... (full corrected test content) ...
### END

Only provide the file(s) that need to change.
"""
        return self.provider.generate(prompt)

    def parse_fix_response(self, response: str) -> dict[str, str]:
        """
        Parses the fix response to extract file contents.
        Returns a dict mapping filename -> content.
        """
        fixes = {}

        # Regex to find file blocks: "### FILE: path" ... content ... "### END"
        pattern = r"### FILE: (.+?)\n(.*?)### END"
        matches = re.findall(pattern, response, re.DOTALL)

        for filename, content in matches:
            filename = filename.strip()
            content = content.strip()
            content = self._strip_markdown_fences(content)
            fixes[filename] = content

        return fixes

    def _strip_markdown_fences(self, code: str) -> str:
        """Removes markdown code fences if present."""
        if code.startswith("```"):
            lines = code.split("\n")
            # Remove first line (```python or similar)
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line if it's a closing fence
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            code = "\n".join(lines)
        return code
