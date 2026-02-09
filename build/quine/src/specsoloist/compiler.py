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
        """
        Initialize the SpecCompiler.

        Args:
            provider: An LLM provider instance implementing the LLMProvider protocol.
            global_context: Optional project-wide context to include in all prompts.
        """
        self.provider = provider
        self.global_context = global_context

    def compile_code(
        self,
        spec: ParsedSpec,
        model: Optional[str] = None
    ) -> str:
        """
        Compile a function/bundle spec to implementation code.

        Constructs a prompt with the spec body, dependency context, and global context,
        then calls the LLM. Returns raw code (markdown fences stripped).

        Args:
            spec: The parsed specification.
            model: Optional model override.

        Returns:
            The generated implementation code with markdown fences stripped.
        """
        language = spec.metadata.language_target or "python"

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
1. Implement the component exactly as described in the specification.
2. Adhere to all behavioral requirements and constraints.
3. Import required types/functions from dependency modules as specified.
4. Output ONLY the raw code for the implementation. Do not wrap in markdown code blocks.
"""
        code = self.provider.generate(prompt, model=model)
        return self._strip_markdown_fences(code)

    def compile_typedef(
        self,
        spec: ParsedSpec,
        model: Optional[str] = None
    ) -> str:
        """
        Compile a type spec to type definition code.

        Prompts the LLM to define types using idiomatic constructs for the target language.
        Returns raw code.

        Args:
            spec: The parsed specification (must be type: typedef or type).
            model: Optional model override.

        Returns:
            The generated type definition code with markdown fences stripped.
        """
        language = spec.metadata.language_target or "python"

        prompt = f"""
You are an expert {language} developer specializing in type systems.
Your task is to define the data types described in the following specification.

# Global Project Context
{self.global_context}

# Type Specification
{spec.body}

# Instructions
1. Define all types exactly as described in the specification.
2. For Python, prefer dataclasses with type hints. Use TypedDict for dictionary-like types.
3. Include all validation constraints from the specification.
4. Add docstrings explaining each type's purpose.
5. Output ONLY the raw code for the type definitions. Do not wrap in markdown code blocks.
6. Include necessary imports (dataclasses, typing, etc.) at the top.
"""
        code = self.provider.generate(prompt, model=model)
        return self._strip_markdown_fences(code)

    def compile_orchestrator(
        self,
        spec: ParsedSpec,
        model: Optional[str] = None
    ) -> str:
        """
        Compile a workflow/orchestrator spec to execution code.

        Extracts step references for context and prompts the LLM to implement the workflow
        with state passing between steps. Returns raw code.

        Args:
            spec: The parsed specification (must be type: workflow or orchestrator).
            model: Optional model override.

        Returns:
            The generated orchestration code with markdown fences stripped.
        """
        language = spec.metadata.language_target or "python"

        # Extract specs used in steps to include in import context
        used_specs = []
        if spec.schema and spec.schema.steps:
            for step in spec.schema.steps:
                if step.spec not in used_specs:
                    used_specs.append(step.spec)

        import_context = "\n".join([f"- This workflow uses components from: {s}" for s in used_specs])

        prompt = f"""
You are an expert {language} developer specializing in multi-agent orchestration.
Your task is to implement the workflow described in the following specification.

# Global Project Context
{self.global_context}

# Components Available
{import_context}

# Orchestration Specification
{spec.body}

# Instructions
1. Implement the orchestration logic as defined in the specification.
2. Handle state passing between workflow steps as specified.
3. Include appropriate error handling and logging.
4. Output ONLY the raw code. Do not wrap in markdown code blocks.
"""
        code = self.provider.generate(prompt, model=model)
        return self._strip_markdown_fences(code)

    def compile_tests(
        self,
        spec: ParsedSpec,
        model: Optional[str] = None
    ) -> str:
        """
        Generate a test suite for a spec.

        Prompts the LLM to write tests covering all scenarios and edge cases from the spec.
        Uses appropriate test framework for the target language (pytest for Python, node:test for TypeScript).
        Returns raw test code.

        Args:
            spec: The parsed specification.
            model: Optional model override.

        Returns:
            The generated test code with markdown fences stripped.
        """
        language = spec.metadata.language_target or "python"
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
3. Implement a test case for EVERY scenario listed in the specification.
4. Implement additional edge cases based on the specification's behavioral requirements.
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
        Generate a fix for failing tests.

        Provides the spec (source of truth), current code, current tests, and error output to the LLM.
        Returns raw response with `### FILE: path` / `### END` markers.

        Args:
            spec: The parsed specification (source of truth).
            code_content: Current implementation code.
            test_content: Current test code.
            error_log: Test failure output.
            model: Optional model override.

        Returns:
            The raw LLM response with FILE markers for patching.
        """
        module_name = spec.metadata.name or spec.path.replace(".spec.md", "")
        language = spec.metadata.language_target or "python"

        # Simple extension mapping
        ext = ".py"
        if language.lower() in ["typescript", "ts"]:
            ext = ".ts"
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

### FILE: path/to/{module_name}{ext}
... (full corrected code content) ...
### END

OR

### FILE: path/to/{test_filename}
... (full corrected test content) ...
### END

Only provide the file(s) that need to change.
"""
        return self.provider.generate(prompt, model=model)

    def parse_fix_response(self, response: str) -> dict[str, str]:
        """
        Parse the LLM fix response to extract file contents.

        Finds all `### FILE: <path>` ... `### END` blocks and returns a dict mapping
        filename to cleaned content (markdown fences stripped).

        Args:
            response: The raw LLM response with FILE markers.

        Returns:
            A dict mapping filename to cleaned content.
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

    def _build_import_context(self, spec: ParsedSpec) -> str:
        """
        Build import instructions from spec dependencies.

        Args:
            spec: The parsed specification.

        Returns:
            A formatted string describing dependencies for the prompt.
        """
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

    def _strip_markdown_fences(self, code: str) -> str:
        """
        Remove markdown code fences if present.

        Handles both triple-backtick fences (with or without language specifier)
        and returns the raw code content.

        Args:
            code: The code potentially wrapped in markdown fences.

        Returns:
            The code with markdown fences removed.
        """
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
