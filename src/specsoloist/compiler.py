"""
Spec compilation: prompt construction and code generation.
"""

import re
from typing import Optional

from .parser import ParsedSpec
from .providers import LLMProvider


class SpecCompiler:
    """Compiles specs to code using an LLM provider."""

    def __init__(self, provider: LLMProvider, global_context: str = ""):
        self.provider = provider
        self.global_context = global_context

    def compile_code(
        self,
        spec: ParsedSpec,
        model: Optional[str] = None
    ) -> str:
        """
        Compiles a spec to implementation code.

        Args:
            spec: The parsed specification.
            model: Optional model override.

        Returns:
            The generated code.
        """
        language = spec.metadata.language_target

        # Build import context from dependencies
        import_context = self._build_import_context(spec)

        prompt = f"""
You are an expert {language} developer.
Your task is to implement the code described in the following specification.

# Global Project Context
{self.global_context}

# Dependencies
{import_context}

# Component Specification
{spec.body}

# Instructions
1. Implement the component exactly as described in the Functional Requirements.
2. Adhere strictly to the Non-Functional Requirements (Performance, Purity).
3. Ensure the code satisfies the Design Contract (Pre/Post-conditions).
4. Import required types/functions from dependency modules as specified.
5. Output ONLY the raw code for the implementation. Do not wrap in markdown code blocks.
"""
        code = self.provider.generate(prompt, model=model)
        return self._strip_markdown_fences(code)

    def compile_typedef(
        self,
        spec: ParsedSpec,
        model: Optional[str] = None
    ) -> str:
        """
        Compiles a typedef spec to type definitions (dataclasses, TypedDicts, etc.).

        Args:
            spec: The parsed specification (must be type: typedef).
            model: Optional model override.

        Returns:
            The generated type definition code.
        """
        language = spec.metadata.language_target

        prompt = f"""
You are an expert {language} developer specializing in type systems.
Your task is to define the data types described in the following specification.

# Global Project Context
{self.global_context}

# Type Specification
{spec.body}

# Instructions
1. Define all types exactly as described in the Interface Specification.
2. For Python, prefer dataclasses with type hints. Use TypedDict for dictionary-like types.
3. Include all validation constraints from the Design Contract as field validators if appropriate.
4. Add docstrings explaining each type's purpose.
5. Output ONLY the raw code for the type definitions. Do not wrap in markdown code blocks.
6. Include necessary imports (dataclasses, typing, etc.) at the top.
"""
        code = self.provider.generate(prompt, model=model)
        return self._strip_markdown_fences(code)

    def _build_import_context(self, spec: ParsedSpec) -> str:
        """Build import instructions from spec dependencies."""
        if not spec.metadata.dependencies:
            return "No external dependencies."

        lines = ["This component depends on the following modules:"]
        for dep in spec.metadata.dependencies:
            if isinstance(dep, dict):
                name = dep.get("name", "")
                from_spec = dep.get("from", "").replace(".spec.md", "")
                if name and from_spec:
                    lines.append(f"- Import `{name}` from `{from_spec}`")
            elif isinstance(dep, str):
                from_spec = dep.replace(".spec.md", "")
                lines.append(f"- Import from `{from_spec}`")

        return "\n".join(lines)

    def compile_tests(
        self,
        spec: ParsedSpec,
        model: Optional[str] = None
    ) -> str:
        """
        Generates a test suite for a spec.

        Args:
            spec: The parsed specification.
            model: Optional model override.

        Returns:
            The generated test code.
        """
        language = spec.metadata.language_target
        module_name = spec.metadata.name or spec.path.replace(".spec.md", "")

        test_instructions = "1. Write a standard test file (e.g., using `pytest` for Python)."
        if language.lower() in ["typescript", "javascript", "ts", "js"]:
            test_instructions = (
                "1. Use the Node.js built-in test runner: `import { describe, it } from 'node:test';` "
                "and `import assert from 'node:assert';`.\n"
                "2. Do NOT use Jest, Mocha, or Chai."
            )

        prompt = f"""
You are an expert QA Engineer specialized in {language}.
Your task is to write a comprehensive unit test suite for the component described below.

# Component Specification
{spec.body}

# Instructions
{test_instructions}
2. The component implementation will be in a module named `{module_name}`. Import it like `from {module_name} import ...`.
3. Implement a test case for EVERY scenario listed in the 'Test Scenarios' section of the spec.
4. Implement additional edge cases based on the 'Design Contract' (Pre/Post-conditions).
5. Output ONLY the raw code.
"""
        code = self.provider.generate(prompt, model=model)
        return self._strip_markdown_fences(code)

    def generate_fix(
        self,
        spec: ParsedSpec,
        code_content: str,
        test_content: str,
        error_log: str,
        model: Optional[str] = None
    ) -> str:
        """
        Generates a fix for failing tests.

        Args:
            spec: The parsed specification (source of truth).
            code_content: Current implementation code.
            test_content: Current test code.
            error_log: Test failure output.
            model: Optional model override.

        Returns:
            The raw LLM response with FILE markers.
        """
        module_name = spec.metadata.name or spec.path.replace(".spec.md", "")
        language = spec.metadata.language_target
        
        # Simple extension mapping (could use config, but this is prompt-side)
        ext = ".py"
        
        if language.lower() in ["typescript", "ts"]:
            ext = ".ts"
            # for TS, test file pattern is usually module.test.ts
            test_filename = f"{module_name}.test.ts"
        else:
            test_filename = f"test_{module_name}.py"

        prompt = f"""
You are a Senior Software Engineer tasked with fixing a build failure.
Analyze the discrepancy between the Code, the Test, and the Specification.

# 1. The Specification (Source of Truth)
{spec.content}

# 2. The Current Implementation ({module_name}{ext})
{code_content}

# 3. The Failing Test Suite ({test_filename})
{test_content}

# 4. The Test Failure Output
{error_log}

# Instructions
1. Analyze why the test failed.
2. Determine if the **Code** is buggy (violates spec) or if the **Test** is wrong (hallucinated expectation).
3. Provide the CORRECTED content for the file that needs fixing.
4. Use the following format for your output so I can apply the patch:

### FILE: build/{module_name}{ext}
... (full corrected code content) ...
### END

OR

### FILE: build/{test_filename}
... (full corrected test content) ...
### END

Only provide the file(s) that need to change.
"""
        return self.provider.generate(prompt, model=model)

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
